import random
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from jobspy import scrape_jobs
from jobspy.linkedin.constant import headers as linkedin_headers
from markdownify import markdownify as md

DB_PATH = Path(__file__).parent / "jobs.db"


def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Инициализирует SQLite базу для дедупликации и хранения результатов."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    # WAL позволяет читать базу параллельно во время записи без блокировок
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            date_posted TEXT,
            matched INTEGER,
            processed_at TEXT
        )
        """
    )
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
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO processed_jobs (job_id, title, company, url, date_posted, matched, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            title,
            company,
            url,
            date_posted,
            1 if matched else 0,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


def fetch_job_description(
    session: requests.Session,
    job_id: str,
    delay_range: tuple[float, float] = (1.5, 2.5),
    max_retries: int = 3,
) -> str | None:
    """
    Догружает полное описание вакансии с паузой и ретраями при 429/502/503.
    Возвращает текст описания (markdown) или None, если карточка временно недоступна.
    """
    raw_id = job_id.removeprefix("li-")
    # Пробуем гостевой API карточки (легче и быстрее полной страницы) и фоллбэк на /jobs/view/
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
                soup = BeautifulSoup(resp.text, "html.parser")
                div = soup.find("div", class_="show-more-less-html__markup")
                if div:
                    return md(str(div)).strip()
                # Если верстка вернулась без блока описания (например, редирект на authwall)
                if "authwall" in resp.url or "login" in resp.url:
                    print(f"  ⚠️ [{job_id}] Редирект на authwall (попытка {attempt}/{max_retries})")
                else:
                    return ""
            elif resp.status_code in (429, 502, 503, 504):
                backoff = attempt * 3.0 + random.uniform(1.0, 2.5)
                print(
                    f"  ⏳ [{job_id}] Статус {resp.status_code} (попытка {attempt}/{max_retries}), "
                    f"ждем {backoff:.1f}с..."
                )
                time.sleep(backoff)
            elif resp.status_code == 404:
                return ""
            else:
                print(f"  ⚠️ [{job_id}] Неожиданный статус {resp.status_code}")
        except requests.RequestException as e:
            backoff = attempt * 2.0
            print(f"  ⚠️ [{job_id}] Ошибка сети: {e} (попытка {attempt}/{max_retries}), ждем {backoff:.1f}с...")
            time.sleep(backoff)

    return None


def fetch_and_filter_jobs(
    search_term: str = "Software Engineer Remote",
    location: str = "EMEA",
    results_wanted: int = 30,
    hours_old: int = 24,
) -> list[dict]:
    conn = init_db()
    processed_ids = get_processed_ids(conn)
    print(f"🗄️ В базе уже обработано вакансий: {len(processed_ids)}")

    # 1. Запрашиваем список вакансий БЕЗ полных описаний (fetch_description=False)
    print(f"🔍 Поиск вакансий '{search_term}' в '{location}' (за последние {hours_old}ч)...")
    jobs: pd.DataFrame = scrape_jobs(
        site_name=["linkedin"],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        fetch_description=False,  # Сначала получаем только заголовки и метаданные
    )

    if jobs.empty:
        print("Новых вакансий не найдено.")
        conn.close()
        return []

    print(f"📦 Найдено карточек в поиске: {len(jobs)}")

    # 2. Дедупликация по job_id и по паре (title, company) — компании часто постят
    # одну и ту же Remote-вакансию на 10 разных стран EMEA с разными job_id
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
        print(f"⏭️ Пропущено уже обработанных ранее вакансий (из БД): {skipped_seen}")

    if unseen_jobs.empty:
        print("Все найденные вакансии уже были обработаны ранее.")
        conn.close()
        return []

    # 3. Первичная фильтрация по заголовку ДО скачивания описания
    exclude_title_words = [
        "intern", "junior", "php", "c++", "wordpress", ".net", "c#", "golang", "rust", "ios", "macos", "android"
    ]
    exclude_pattern = "|".join(re.escape(w) for w in exclude_title_words)
    title_mask = ~unseen_jobs["title"].fillna("").str.lower().str.contains(exclude_pattern, regex=True)

    # Вакансии, отсеянные по заголовку, сразу помечаем в БД как обработанные (matched=False),
    # чтобы больше никогда к ним не возвращаться
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
        )

    candidates = unseen_jobs[title_mask].copy()
    print(
        f"🧹 Отсеяно по заголовку: {len(rejected_by_title)} | "
        f"Кандидатов для загрузки описания: {len(candidates)}"
    )

    # 4. Догружаем описания с паузой 1.5–2.5 сек и ретраями только для кандидатов
    # Используем границы слов (\b), чтобы 'java' не матчилось внутри 'javascript'
    required_keywords = ["kotlin", "java", "spring", "python", "langgraph", "microservices"]
    required_pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(w) for w in required_keywords) + r")\b",
        re.IGNORECASE,
    )

    results = []
    session = requests.Session()

    for idx, (_, row) in enumerate(candidates.iterrows(), start=1):
        job_id = str(row.get("id"))
        title = str(row.get("title", ""))
        company = str(row.get("company", ""))
        job_url = str(row.get("job_url", ""))
        date_posted = str(row.get("date_posted", ""))

        print(f"📥 [{idx}/{len(candidates)}] Загрузка описания: {title} @ {company} ({job_id})...")
        description = fetch_job_description(session, job_id)

        if description is None:
            # Если даже после ретраев LinkedIn не отдал карточку — НЕ записываем в БД,
            # чтобы попробовать снова при следующем запуске
            print(f"  ❌ Не удалось загрузить описание для {job_id}, оставляем на следующий запуск.")
            continue

        is_match = bool(required_pattern.search(description))
        mark_job_processed(
            conn,
            job_id=job_id,
            title=title,
            company=company,
            url=job_url,
            date_posted=date_posted,
            matched=is_match,
        )

        if is_match:
            clean_snippet = " ".join(description.split())[:300]
            results.append(
                {
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "url": job_url,
                    "date_posted": date_posted,
                    "description_snippet": clean_snippet + ("..." if len(clean_snippet) >= 300 else ""),
                }
            )
            print(f"  ✅ Подходит по стеку!")
        else:
            print(f"  ➖ Стек не совпал.")

    conn.close()
    return results


if __name__ == "__main__":
    matched = fetch_and_filter_jobs()
    print(f"\n🎯 Итого новых подходящих вакансий за этот запуск: {len(matched)}\n")
    for job in matched:
        print(f"🔥 {job['title']} @ {job['company']} ({job['date_posted']})")
        print(f"🔗 {job['url']}")
        print(f"📝 {job['description_snippet']}\n")
