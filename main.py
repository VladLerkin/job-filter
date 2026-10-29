from collections.abc import Callable
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import re
import sqlite3
import time

from bs4 import BeautifulSoup
from jobspy import scrape_jobs
from jobspy.linkedin.constant import headers as linkedin_headers
from jobspy.linkedin.util import criteria
from markdownify import markdownify as md
import pandas as pd
import requests

from agy_enrich import DEFAULT_MODEL, enrich_job_with_agy
from enrichment_schema import JobEnrichment
from skill_scorer import SkillScoreResult, score_vacancy_by_skill

DB_PATH = Path(__file__).parent / "jobs.db"


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Инициализирует SQLite базу и выполняет мягкую миграцию новых колонок."""
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            date_posted TEXT,
            seniority_level TEXT,
            employment_type TEXT,
            job_function TEXT,
            industry TEXT,
            salary TEXT,
            description TEXT,
            matched INTEGER,
            reject_reason TEXT,
            processed_at TEXT,
            enrichment_json TEXT,
            score INTEGER,
            tier TEXT,
            score_details_json TEXT,
            user_status TEXT DEFAULT 'new'
        )
        """
    )

    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(processed_jobs)").fetchall()
    }
    new_cols = {
        "seniority_level": "TEXT",
        "employment_type": "TEXT",
        "job_function": "TEXT",
        "industry": "TEXT",
        "salary": "TEXT",
        "description": "TEXT",
        "reject_reason": "TEXT",
        "enrichment_json": "TEXT",
        "score": "INTEGER",
        "tier": "TEXT",
        "score_details_json": "TEXT",
        "user_status": "TEXT DEFAULT 'new'",
    }
    for col_name, col_type in new_cols.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE processed_jobs ADD COLUMN {col_name} {col_type}")

    conn.commit()
    return conn


def get_processed_ids(conn: sqlite3.Connection) -> set[str]:
    cursor = conn.execute("SELECT job_id FROM processed_jobs")
    return {row[0] for row in cursor.fetchall()}


def mark_job_processed(
    conn: sqlite3.Connection,
    job_id: str,
    title: str,
    company: str,
    url: str,
    date_posted: str,
    matched: bool,
    reject_reason: str | None = None,
    seniority_level: str | None = None,
    employment_type: str | None = None,
    job_function: str | None = None,
    industry: str | None = None,
    salary: str | None = None,
    description: str | None = None,
    enrichment_json: str | None = None,
    score: int | None = None,
    tier: str | None = None,
    score_details_json: str | None = None,
) -> None:
    # Сохраняем существующий user_status, если запись обновляется
    cur = conn.execute("SELECT user_status FROM processed_jobs WHERE job_id = ?", (job_id,)).fetchone()
    user_status = (cur[0] if cur and cur[0] else "new")

    conn.execute(
        """
        INSERT OR REPLACE INTO processed_jobs (
            job_id, title, company, url, date_posted,
            seniority_level, employment_type, job_function, industry, salary,
            description, matched, reject_reason, processed_at,
            enrichment_json, score, tier, score_details_json, user_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            title,
            company,
            url,
            date_posted,
            seniority_level,
            employment_type,
            job_function,
            industry,
            salary,
            description,
            1 if matched else 0,
            reject_reason,
            datetime.now(timezone.utc).isoformat(),
            enrichment_json,
            score,
            tier,
            score_details_json,
            user_status,
        ),
    )
    conn.commit()


def update_job_enrichment_and_score(
    conn: sqlite3.Connection,
    job_id: str,
    enrichment: JobEnrichment,
    score_res: SkillScoreResult,
) -> None:
    reject_reason = None
    matched = 1
    if not score_res.geo_passed:
        matched = 0
        reject_reason = score_res.geo_reject_reason or "rejected_geo"
    elif score_res.score < 50:
        matched = 0
        reject_reason = f"low_score:{score_res.score}"

    conn.execute(
        """
        UPDATE processed_jobs
        SET enrichment_json = ?,
            score = ?,
            tier = ?,
            score_details_json = ?,
            matched = ?,
            reject_reason = COALESCE(?, reject_reason)
        WHERE job_id = ?
        """,
        (
            enrichment.model_dump_json(),
            score_res.score,
            score_res.tier,
            score_res.model_dump_json(),
            matched,
            reject_reason,
            job_id,
        ),
    )
    conn.commit()


def fetch_job_details(
    session: requests.Session,
    job_id: str,
    delay_range: tuple[float, float] = (1.5, 2.5),
    max_retries: int = 3,
) -> dict[str, str | None] | None:
    """
    Догружает полное описание вакансии и метаданные карточки (Seniority, Employment type,
    Job function, Industries, Salary) с паузой и ретраями при 429/502/503.
    """
    raw_id = job_id.removeprefix("li-")
    urls = [
        f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{raw_id}",
        f"https://www.linkedin.com/jobs/view/{raw_id}",
    ]

    for attempt in range(1, max_retries + 1):
        time.sleep(random.uniform(*delay_range))
        url = urls[(attempt - 1) % len(urls)]
        try:
            resp = session.get(url, headers=linkedin_headers, timeout=15)
            if resp.status_code == 200:
                if "authwall" in resp.url or "login" in resp.url:
                    print(f"  ⚠️ [{job_id}] Редирект на authwall (попытка {attempt}/{max_retries})")
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                div = soup.find("div", class_="show-more-less-html__markup")
                description = md(str(div)).strip() if div else ""

                salary_tag = soup.find("div", class_="compensation__salary")
                salary_text = " ".join(salary_tag.get_text().split()) if salary_tag else None

                return {
                    "description": description,
                    "seniority_level": criteria(soup, "Seniority level"),
                    "employment_type": criteria(soup, "Employment type"),
                    "job_function": criteria(soup, "Job function"),
                    "industry": criteria(soup, "Industries"),
                    "salary": salary_text,
                }
            elif resp.status_code in (429, 502, 503, 504):
                backoff = attempt * 3.0 + random.uniform(1.0, 2.5)
                print(
                    f"  ⏳ [{job_id}] Статус {resp.status_code} (попытка {attempt}/{max_retries}), "
                    f"ждем {backoff:.1f}с..."
                )
                time.sleep(backoff)
            elif resp.status_code == 404:
                return {
                    "description": "",
                    "seniority_level": None,
                    "employment_type": None,
                    "job_function": None,
                    "industry": None,
                    "salary": None,
                }
            else:
                print(f"  ⚠️ [{job_id}] Неожиданный статус {resp.status_code}")
        except requests.RequestException as e:
            backoff = attempt * 2.0
            print(f"  ⚠️ [{job_id}] Ошибка сети: {e} (попытка {attempt}/{max_retries}), ждем {backoff:.1f}с...")
            time.sleep(backoff)

    return None


def enrich_and_score_pending_jobs(
    conn: sqlite3.Connection,
    model: str = DEFAULT_MODEL,
    limit: int = 30,
    on_progress: Callable[[str], None] | None = None,
) -> int:
    """
    Находит в БД вакансии, прошедшие базовый фильтр (matched=1 и description IS NOT NULL),
    у которых еще нет enrichment_json, прогоняет их через локальный agy CLI (JobEnrichment)
    и оценивает по скиллу hirify-vacancy-filter.
    """
    def emit(msg: str) -> None:
        print(msg)
        if on_progress:
            on_progress(msg)

    rows = conn.execute(
        """
        SELECT job_id, title, company, url, date_posted, seniority_level, industry, salary, description
        FROM processed_jobs
        WHERE description IS NOT NULL
          AND description != ''
          AND enrichment_json IS NULL
          AND (reject_reason IS NULL OR reject_reason = '')
        ORDER BY processed_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    if not rows:
        emit("✨ Все кандидаты в базе уже обогащены через LLM.")
        return 0

    emit(f"🤖 Запуск LLM-обогащения ({model}) и скоринга для {len(rows)} вакансий...")
    enriched_count = 0

    for idx, row in enumerate(rows, start=1):
        job_id = row["job_id"]
        title = row["title"] or ""
        company = row["company"] or ""
        desc = row["description"] or ""

        emit(f"🧠 [{idx}/{len(rows)}] ИИ-разбор: {title} @ {company} ({job_id})...")
        try:
            enrichment = enrich_job_with_agy(
                title=title,
                company=company,
                location="EMEA / Remote",
                description=desc,
                model=model,
            )
            score_res = score_vacancy_by_skill(
                title=title,
                company=company,
                date_posted=row["date_posted"],
                seniority_level=row["seniority_level"],
                industry=row["industry"],
                salary_text=row["salary"],
                description=desc,
                enrichment=enrichment,
            )
            update_job_enrichment_and_score(conn, job_id, enrichment, score_res)
            enriched_count += 1
            badge = (
                "🟢 TOP"
                if score_res.match_category == "top"
                else "🟡 GOOD"
                if score_res.match_category == "good"
                else "🔴 LOW/GEO"
            )
            emit(
                f"  ↳ {badge} | Score: {score_res.score}/100 | {score_res.tier} | "
                f"Совпало: {len(score_res.matched_skills)}, Пробелов: {len(score_res.missing_skills)}"
            )
        except Exception as e:
            emit(f"  ⚠️ Ошибка LLM для {job_id}: {e}")

    return enriched_count


def fetch_and_filter_jobs(
    search_terms: str | list[str] = (
        "Agentic Engineer Remote",
        "AI Agent Engineer Remote",
        "Software Engineer Remote",
    ),
    location: str = "EMEA",
    results_wanted: int = 30,
    hours_old: int = 4,
    easy_apply: bool | None = None,
    linkedin_company_ids: list[int] | None = None,
    run_llm_enrichment: bool = True,
    llm_model: str = DEFAULT_MODEL,
    llm_limit: int = 25,
    on_progress: Callable[[str], None] | None = None,
) -> list[dict]:
    def emit(msg: str) -> None:
        print(msg)
        if on_progress:
            on_progress(msg)

    conn = init_db()
    processed_ids = get_processed_ids(conn)
    emit(f"🗄️ В базе уже обработано вакансий: {len(processed_ids)}")

    if isinstance(search_terms, str):
        terms = [t.strip() for t in search_terms.split(",") if t.strip()]
    else:
        terms = list(search_terms)

    # 1. Запрашиваем список вакансий по каждому запросу БЕЗ полных описаний (fetch_description=False)
    frames: list[pd.DataFrame] = []
    easy_label = " [⚡ Только Easy Apply]" if easy_apply else ""
    for idx, term in enumerate(terms):
        if idx > 0:
            time.sleep(random.uniform(2.0, 4.0))
        emit(f"🔍 Поиск вакансий '{term}' в '{location}' (за последние {hours_old}ч){easy_label}...")
        try:
            df: pd.DataFrame = scrape_jobs(
                site_name=["linkedin"],
                search_term=term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                easy_apply=easy_apply,
                linkedin_company_ids=linkedin_company_ids,
                fetch_description=False,
            )
        except Exception as e:
            emit(f"  ⚠️ Ошибка поиска для '{term}': {e}")
            df = pd.DataFrame()

        if not df.empty:
            emit(f"  ↳ Найдено по запросу '{term}': {len(df)}")
            frames.append(df)
        else:
            emit(f"  ↳ По запросу '{term}' вакансий не найдено.")

    if frames:
        jobs = pd.concat(frames, ignore_index=True)
        emit(f"📦 Суммарно карточек со всех запросов: {len(jobs)}")

        # 2. Дедупликация по job_id и по паре (title, company)
        jobs = jobs.drop_duplicates(subset=["id"]).copy()
        jobs["_dedup_key"] = (
            jobs["title"].fillna("").str.strip().str.lower()
            + "::"
            + jobs["company"].fillna("").str.strip().str.lower()
        )
        jobs = jobs.drop_duplicates(subset=["_dedup_key"]).drop(columns=["_dedup_key"]).copy()

        new_jobs_mask = ~jobs["id"].astype(str).isin(processed_ids)
        unseen_jobs = jobs[new_jobs_mask].copy()
        skipped_seen = len(jobs) - len(unseen_jobs)
        if skipped_seen:
            emit(f"⏭️ Пропущено уже обработанных ранее вакансий (из БД): {skipped_seen}")

        if not unseen_jobs.empty:
            # 3. Первичная фильтрация по заголовку ДО скачивания описания
            exclude_title_words = [
                "intern", "junior", "php", "c++", "wordpress", ".net", "c#", "golang", "rust", "ios", "macos", "android"
            ]
            exclude_pattern = "|".join(re.escape(w) for w in exclude_title_words)
            title_mask = ~unseen_jobs["title"].fillna("").str.lower().str.contains(exclude_pattern, regex=True)

            rejected_by_title = unseen_jobs[~title_mask]
            for _, row in rejected_by_title.iterrows():
                mark_job_processed(
                    conn,
                    job_id=str(row.get("id")),
                    title=str(row.get("title", "")),
                    company=str(row.get("company", "")),
                    url=str(row.get("job_url", "")),
                    date_posted=str(row.get("date_posted", "")),
                    matched=False,
                    reject_reason="excluded_title",
                )

            candidates = unseen_jobs[title_mask].copy()
            emit(
                f"🧹 Отсеяно по заголовку: {len(rejected_by_title)} | "
                f"Кандидатов для загрузки описания: {len(candidates)}"
            )

            # 4. Догружаем описания и критерии карточки с паузой 1.5–2.5 сек
            required_keywords = ["kotlin", "java", "spring", "python", "langgraph", "microservices", "llm", "agentic", "rag"]
            required_pattern = re.compile(
                r"\b(?:" + "|".join(re.escape(w) for w in required_keywords) + r")\b",
                re.IGNORECASE,
            )

            excluded_seniorities = {"internship", "entry level"}
            excluded_industries = {"staffing and recruiting"}

            session = requests.Session()

            for idx, (_, row) in enumerate(candidates.iterrows(), start=1):
                job_id = str(row.get("id"))
                title = str(row.get("title", ""))
                company = str(row.get("company", ""))
                job_url = str(row.get("job_url", ""))
                date_posted = str(row.get("date_posted", ""))

                emit(f"📥 [{idx}/{len(candidates)}] Загрузка карточки: {title} @ {company} ({job_id})...")
                details = fetch_job_details(session, job_id)

                if details is None:
                    emit(f"  ❌ Не удалось загрузить карточку {job_id}, оставляем на следующий запуск.")
                    continue

                description = details["description"] or ""
                seniority = details["seniority_level"]
                employment_type = details["employment_type"]
                job_function = details["job_function"]
                industry = details["industry"]
                salary = details["salary"]

                reject_reason = None
                if seniority and seniority.strip().lower() in excluded_seniorities:
                    reject_reason = f"excluded_seniority:{seniority}"
                elif industry and industry.strip().lower() in excluded_industries:
                    reject_reason = f"excluded_industry:{industry}"
                elif not required_pattern.search(description):
                    reject_reason = "missing_keywords"

                is_match = reject_reason is None

                mark_job_processed(
                    conn,
                    job_id=job_id,
                    title=title,
                    company=company,
                    url=job_url,
                    date_posted=date_posted,
                    matched=is_match,
                    reject_reason=reject_reason,
                    seniority_level=seniority,
                    employment_type=employment_type,
                    job_function=job_function,
                    industry=industry,
                    salary=salary,
                    description=description,
                )

                if is_match:
                    emit(f"  ✅ Прошла базовый фильтр ({seniority or 'N/A'} | {industry or 'N/A'})")
                else:
                    emit(f"  ➖ Отклонено ({reject_reason}).")
        else:
            emit("Все найденные карточки из поиска уже были в БД.")
    else:
        emit("Поисковая выдача пуста.")

    # 5. Запускаем Шаг 1 (JobEnrichment через agy CLI) + Шаг 2 (Скоринг по скиллу)
    if run_llm_enrichment:
        enrich_and_score_pending_jobs(conn, model=llm_model, limit=llm_limit, on_progress=on_progress)

    # Возвращаем отранжированный сухой остаток
    final_rows = conn.execute(
        """
        SELECT * FROM processed_jobs
        WHERE matched = 1 AND score IS NOT NULL AND score >= 50
        ORDER BY score DESC, date_posted DESC
        """
    ).fetchall()
    results = [dict(r) for r in final_rows]
    conn.close()
    return results


if __name__ == "__main__":
    matched = fetch_and_filter_jobs()
    print(f"\n🎯 Итого вакансий в сухом остатке (Score >= 50): {len(matched)}\n")
    for job in matched:
        print(f"🔥 [{job.get('score')}/100 | {job.get('tier')}] {job['title']} @ {job['company']} ({job['date_posted']})")
        print(f"🔗 {job['url']}\n")
