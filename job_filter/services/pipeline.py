"""Основной поисковый и оценочный пайплайн: сбор скрапингом, первичный фильтр, дозагрузка описания, обогащение через LLM и скоринг."""
from collections.abc import Callable
import logging
import random
import re
import sqlite3
import time
from typing import Any
import pandas as pd
import requests

from job_filter import config
from job_filter.db.connection import connect
from job_filter.llm.job_enricher import enrich_job, load_resume_text
from job_filter.repositories import blacklist_repo, jobs_repo
from job_filter.scoring.scorer import score_vacancy_by_skill
from job_filter.scraping.linkedin import fetch_job_details
from job_filter.scraping.providers import scrape_site
from job_filter.utils.urls import extract_root_domain

logger = logging.getLogger(__name__)


def enrich_and_score_pending_jobs(
    conn: sqlite3.Connection,
    model: str = config.DEFAULT_MODEL,
    limit: int = 30,
    on_progress: Callable[[str], None] | None = None,
) -> int:
    """
    Находит в БД вакансии, прошедшие базовый фильтр (matched=1 и description IS NOT NULL),
    у которых еще нет enrichment_json, прогоняет их через локальный agy CLI (JobEnrichment)
    и оценивает по скоринговой модели.
    """
    def emit(msg: str) -> None:
        logger.info("%s", msg)
        if on_progress:
            on_progress(msg)

    rows = jobs_repo.list_pending_enrichment(conn, limit)

    if not rows:
        emit("✨ Все кандидаты в базе уже обогащены через LLM.")
        return 0

    emit(f"🤖 Запуск LLM-обогащения ({model}) и скоринга для {len(rows)} вакансий...")
    enriched_count = 0
    resume_text = load_resume_text()

    for idx, row in enumerate(rows, start=1):
        job_id = row["job_id"]
        title = row["title"] or ""
        company = row["company"] or ""
        desc = row["description"] or ""

        emit(f"🧠 [{idx}/{len(rows)}] ИИ-разбор: {title} @ {company} ({job_id})...")
        try:
            enrichment = enrich_job(
                title=title,
                company=company,
                location="EMEA / Remote",
                description=desc,
                model=model,
                resume=resume_text,
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
                conn=conn,
            )
            matched = 0 if (not score_res.geo_passed or score_res.score < 50) else 1
            reject_reason = (
                score_res.geo_reject_reason if not score_res.geo_passed else (f"low_score:{score_res.score}" if score_res.score < 50 else None)
            )
            jobs_repo.update_enrichment_and_score(
                conn,
                job_id=job_id,
                enrichment_json=enrichment.model_dump_json(),
                score=score_res.score,
                tier=score_res.tier,
                score_details_json=score_res.model_dump_json(),
                matched=matched,
                reject_reason=reject_reason,
            )
            conn.commit()
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


def _save_processed_job(
    conn: sqlite3.Connection,
    job_id: str,
    title: str,
    company: str,
    url: str,
    date_posted: str,
    matched: bool,
    site: str = "linkedin",
    location: str | None = None,
    is_remote: bool | None = None,
    reject_reason: str | None = None,
    seniority_level: str | None = None,
    employment_type: str | None = None,
    job_function: str | None = None,
    industry: str | None = None,
    salary: str | None = None,
    description: str | None = None,
    apply_url: str | None = None,
    ats_domain: str | None = None,
) -> None:
    cur = jobs_repo.get_job(conn, job_id)
    user_status = (cur.get("user_status") if cur and cur.get("user_status") else "new")
    existing_apply_url = cur.get("apply_url") if cur else None
    existing_ats_domain = cur.get("ats_domain") if cur else None

    final_apply_url = apply_url or existing_apply_url
    final_ats_domain = ats_domain or extract_root_domain(final_apply_url) or existing_ats_domain
    if not final_ats_domain and company:
        comp_info = blacklist_repo.get_company_ats(conn, company.strip().lower())
        if comp_info:
            final_ats_domain = comp_info.get("ats_domain")

    jobs_repo.replace_job(
        conn,
        {
            "job_id": job_id,
            "site": site or "linkedin",
            "location": location,
            "is_remote": (1 if is_remote else 0) if is_remote is not None else None,
            "title": title,
            "company": company,
            "url": url,
            "date_posted": date_posted,
            "seniority_level": seniority_level,
            "employment_type": employment_type,
            "job_function": job_function,
            "industry": industry,
            "salary": salary,
            "description": description,
            "matched": 1 if matched else 0,
            "reject_reason": reject_reason,
            "user_status": user_status,
            "apply_url": final_apply_url,
            "ats_domain": final_ats_domain,
        },
    )
    conn.commit()


def fetch_and_filter_jobs(
    search_terms: str | list[str] = config.DEFAULT_SEARCH_TERMS,
    site_names: list[str] | None = None,
    location: str = "EMEA",
    country_indeed: str = "uk",
    results_wanted: int = 30,
    hours_old: int = 4,
    easy_apply: bool | None = None,
    linkedin_company_ids: list[int] | None = None,
    run_llm_enrichment: bool = True,
    llm_model: str = config.DEFAULT_MODEL,
    llm_limit: int = 25,
    on_progress: Callable[[str], None] | None = None,
) -> list[dict]:
    def emit(msg: str) -> None:
        logger.info("%s", msg)
        if on_progress:
            on_progress(msg)

    conn = connect()
    processed_ids = jobs_repo.get_processed_ids(conn)
    emit(f"🗄️ В базе уже обработано вакансий: {len(processed_ids)}")

    if isinstance(search_terms, str):
        terms = [t.strip() for t in search_terms.split(",") if t.strip()]
    else:
        terms = list(search_terms)

    sites = [s.strip().lower() for s in (site_names or ["linkedin"]) if s.strip()]
    site = sites[0] if sites else "linkedin"

    frames: list[pd.DataFrame] = []
    easy_label = " [⚡ Только Easy Apply]" if easy_apply else ""

    for idx, term in enumerate(terms):
        if idx > 0:
            time.sleep(random.uniform(2.0, 4.0))

        try:
            emit(f"🔍 Поиск [{site}] '{term}' в '{location}' (за последние {hours_old}ч){easy_label}...")
            df = scrape_site(
                site=site,
                term=term,
                location=location,
                country_indeed=country_indeed,
                results_wanted=results_wanted,
                hours_old=hours_old,
                easy_apply=easy_apply,
                linkedin_company_ids=linkedin_company_ids,
            )

            site_errors = (df.attrs or {}).get("errors") or {}
            for err_site, err_msg in site_errors.items():
                emit(f"  ⚠️ [{err_site}] Сообщение провайдера: {err_msg}")

            if not df.empty:
                emit(f"  ↳ [{site}] Найдено по '{term}': {len(df)}")
                frames.append(df)
            else:
                emit(f"  ↳ [{site}] По '{term}' вакансий не найдено.")
        except Exception as e:
            emit(f"  ⚠️ [{site}] Ошибка поиска для '{term}': {e}")

    new_matches_count = 0
    if frames:
        jobs = pd.concat(frames, ignore_index=True)
        emit(f"📦 Суммарно карточек со всех запросов: {len(jobs)}")

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
            exclude_pattern = "|".join(re.escape(w) for w in config.EXCLUDED_TITLE_WORDS)
            title_mask = ~unseen_jobs["title"].fillna("").str.lower().str.contains(exclude_pattern, regex=True)

            rejected_by_title = unseen_jobs[~title_mask]
            for _, row in rejected_by_title.iterrows():
                raw_loc = row.get("location")
                loc_str = str(raw_loc) if pd.notna(raw_loc) and raw_loc else None
                raw_rem = row.get("is_remote")
                is_rem_val = bool(raw_rem) if pd.notna(raw_rem) else None
                _save_processed_job(
                    conn,
                    job_id=str(row.get("id")),
                    site=str(row.get("site") or "linkedin"),
                    location=loc_str,
                    is_remote=is_rem_val,
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

            required_pattern = re.compile(
                r"\b(?:" + "|".join(re.escape(w) for w in config.REQUIRED_DESCRIPTION_KEYWORDS) + r")\b",
                re.IGNORECASE,
            )

            session = requests.Session()

            for idx, (_, row) in enumerate(candidates.iterrows(), start=1):
                job_id = str(row.get("id"))
                site_val = str(row.get("site") or ("linkedin" if job_id.startswith("li-") else "other"))
                raw_loc = row.get("location")
                loc_str = str(raw_loc) if pd.notna(raw_loc) and raw_loc else None
                raw_rem = row.get("is_remote")
                is_rem_val = bool(raw_rem) if pd.notna(raw_rem) else None
                title = str(row.get("title", ""))
                company = str(row.get("company", ""))
                job_url = str(row.get("job_url", ""))
                date_posted = str(row.get("date_posted", ""))

                if site_val == "linkedin" or job_id.startswith("li-"):
                    emit(f"📥 [{idx}/{len(candidates)}] [linkedin] Загрузка карточки: {title} @ {company} ({job_id})...")
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
                    apply_url = details.get("apply_url")
                else:
                    emit(f"📥 [{idx}/{len(candidates)}] [{site_val}] Обработка карточки: {title} @ {company} ({job_id})...")
                    raw_desc = row.get("description")
                    description = str(raw_desc) if pd.notna(raw_desc) and raw_desc else ""
                    raw_level = row.get("job_level")
                    seniority = str(raw_level) if pd.notna(raw_level) and raw_level else None
                    raw_type = row.get("job_type")
                    employment_type = str(raw_type) if pd.notna(raw_type) and raw_type else None
                    raw_func = row.get("job_function")
                    job_function = str(raw_func) if pd.notna(raw_func) and raw_func else None
                    raw_ind = row.get("company_industry")
                    industry = str(raw_ind) if pd.notna(raw_ind) and raw_ind else None
                    raw_direct = row.get("job_url_direct")
                    apply_url = str(raw_direct) if pd.notna(raw_direct) and raw_direct else None

                    min_amt = row.get("min_amount")
                    max_amt = row.get("max_amount")
                    curr = row.get("currency") or "$"
                    interval = row.get("interval") or "yr"
                    if pd.notna(min_amt) and pd.notna(max_amt) and (min_amt or max_amt):
                        salary = f"{curr}{min_amt:,.0f} - {curr}{max_amt:,.0f}/{interval}"
                    else:
                        salary = None

                reject_reason = None
                if seniority and seniority.strip().lower() in config.EXCLUDED_SENIORITIES:
                    reject_reason = f"excluded_seniority:{seniority}"
                elif industry and industry.strip().lower() in config.EXCLUDED_INDUSTRIES:
                    reject_reason = f"excluded_industry:{industry}"
                elif not required_pattern.search(description):
                    reject_reason = "missing_keywords"

                is_match = reject_reason is None

                _save_processed_job(
                    conn,
                    job_id=job_id,
                    site=site_val,
                    location=loc_str,
                    is_remote=is_rem_val,
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
                    apply_url=apply_url,
                )

                if is_match:
                    new_matches_count += 1
                    emit(f"  ✅ Прошла базовый фильтр ({seniority or 'N/A'} | {industry or 'N/A'})")
                else:
                    emit(f"  ➖ Отклонено ({reject_reason}).")
        else:
            emit("Все найденные карточки из поиска уже были в БД.")
    else:
        emit("Поисковая выдача пуста.")

    if run_llm_enrichment:
        if new_matches_count > 0:
            enrich_and_score_pending_jobs(conn, model=llm_model, limit=llm_limit, on_progress=on_progress)
        else:
            emit("⏭️ Новых кандидатов для ИИ-оценки не появилось — запуск LLM пропущен.")

    results = jobs_repo.list_final_matches(conn, min_score=config.GOOD_SCORE_THRESHOLD)
    conn.close()
    return results
