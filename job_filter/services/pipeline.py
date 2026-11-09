"""Основной поисковый и оценочный пайплайн: сбор скрапингом, первичный фильтр, дозагрузка описания, обогащение через LLM и скоринг."""
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import logging
import math
import random
import re
import sqlite3
import threading
import time
from typing import Any
import pandas as pd
import requests

from job_filter import config
from job_filter.db.connection import connect
from job_filter.llm.job_enricher import enrich_job, load_candidate_context
from job_filter.repositories import blacklist_repo, candidate_repo, jobs_repo
from job_filter.scoring.matrix import get_skill_matrix
from job_filter.scoring.scorer import score_vacancy_by_skill
from job_filter.scraping.linkedin import fetch_job_details
from job_filter.scraping.providers import normalize_indeed_country, scrape_site
from job_filter.utils.urls import extract_root_domain

logger = logging.getLogger(__name__)


def enrich_and_score_pending_jobs(
    conn: sqlite3.Connection,
    model: str = config.DEFAULT_MODEL,
    limit: int = 50,
    on_progress: Callable[[str], None] | None = None,
    cancel_event: threading.Event | None = None,
    max_workers: int | None = None,
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

    workers = max(1, max_workers if max_workers is not None else config.LLM_ENRICH_WORKERS)
    emit(f"🤖 Запуск LLM-обогащения ({model}, воркеров: {workers}) и скоринга для {len(rows)} вакансий...")
    enriched_count = 0

    # Загружаем контекст кандидата, гео-преференции и матрицу навыков ОДИН раз перед циклом
    resume_text, geo_context = load_candidate_context()
    matrix = get_skill_matrix(conn)
    geo_preferences = candidate_repo.get_settings(conn).get("geo_preferences")

    def _run_single_enrich(idx_and_row: tuple[int, sqlite3.Row]):
        idx, r = idx_and_row
        if cancel_event and cancel_event.is_set():
            return idx, r, None, InterruptedError("Остановлено пользователем")
        jid = r["job_id"]
        t = r["title"] or ""
        c = r["company"] or ""
        d = r["description"] or ""
        j_loc = r["location"] if ("location" in r.keys() and r["location"]) else "Remote"
        emit(f"🧠 [{idx}/{len(rows)}] ИИ-разбор: {t} @ {c} ({jid})...")
        try:
            enr = enrich_job(
                title=t,
                company=c,
                location=j_loc,
                description=d,
                model=model,
                resume=resume_text,
                geo_context=geo_context,
            )
            return idx, r, enr, None
        except Exception as exc:
            return idx, r, None, exc

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_run_single_enrich, (idx, row)) for idx, row in enumerate(rows, start=1)]
        for fut in as_completed(futures):
            if cancel_event and cancel_event.is_set():
                emit("⏹️ Обогащение остановлено пользователем.")
                break
            idx, row, enrichment, err = fut.result()
            job_id = row["job_id"]
            title = row["title"] or ""
            company = row["company"] or ""
            desc = row["description"] or ""
            if err is not None:
                if not isinstance(err, InterruptedError):
                    emit(f"  ⚠️ Ошибка LLM для {job_id}: {err}")
                continue
            try:
                job_loc = row["location"] if ("location" in row.keys() and row["location"]) else "Remote"
                is_rem_val = row["is_remote"] if ("is_remote" in row.keys() and row["is_remote"] is not None) else None
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
                    matrix=matrix,
                    geo_preferences=geo_preferences,
                    job_location=job_loc,
                    is_remote=is_rem_val,
                )
                fair_thr = config.FAIR_SCORE_THRESHOLD
                matched = 0 if (not score_res.geo_passed or score_res.score < fair_thr) else 1
                reject_reason = (
                    score_res.geo_reject_reason
                    if not score_res.geo_passed
                    else (f"low_score:{score_res.score}" if score_res.score < fair_thr else None)
                )
                # Запись в SQLite выполняется строго в основном потоке пайплайна
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
                    else "🟠 FAIR"
                    if score_res.match_category == "fair"
                    else "🔴 LOW/GEO"
                )
                emit(
                    f"  ↳ [{job_id}] {badge} | Score: {score_res.score}/100 | {score_res.tier} | "
                    f"Совпало: {len(score_res.matched_skills)}, Пробелов: {len(score_res.missing_skills)}"
                )
            except Exception as e:
                emit(f"  ⚠️ Ошибка сохранения скоринга для {job_id}: {e}")

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
    user_reject_reason = cur.get("user_reject_reason") if cur else None
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
            "user_reject_reason": user_reject_reason,
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
    results_wanted: int = 50,
    hours_old: int = 4,
    easy_apply: bool | None = None,
    linkedin_company_ids: list[int] | None = None,
    run_llm_enrichment: bool = True,
    llm_model: str = config.DEFAULT_MODEL,
    llm_limit: int = 50,
    on_progress: Callable[[str], None] | None = None,
    hirify_mode: str = "feeds",
    hirify_feed_id: int | str | None = None,
    cancel_event: threading.Event | None = None,
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

    if site == "hirify" and hirify_mode == "feeds":
        from job_filter.scraping.hirify_adapter import HirifyClient, scrape_hirify_feed
        client = HirifyClient()
        if not client.is_configured():
            emit("⚠️ HIRIFY_API_KEY не установлен. Укажите ключ в файле .env.")
        else:
            try:
                feeds = client.get_feeds()
                active_feeds = [f for f in feeds if f.get("is_active")]
                target_feeds = []

                if hirify_feed_id is not None and str(hirify_feed_id).strip() not in ("", "all_active", "all"):
                    try:
                        fid_int = int(hirify_feed_id)
                        target_feeds = [f for f in feeds if f.get("id") == fid_int]
                        if not target_feeds:
                            target_feeds = [{"id": fid_int, "name": f"Фильтр #{fid_int}"}]
                    except ValueError:
                        target_feeds = active_feeds
                else:
                    target_feeds = active_feeds

                emit(f"🔍 [hirify] Поиск по сохранённым фильтрам ({len(target_feeds)} шт., за последние {hours_old}ч)...")
                for f_info in target_feeds:
                    fid = f_info.get("id")
                    fname = f_info.get("name") or f"Feed #{fid}"
                    emit(f"  ↳ Сбор по фильтру '{fname}' (ID: {fid})...")
                    df = scrape_hirify_feed(
                        feed_id=fid,
                        results_wanted=results_wanted,
                        hours_old=hours_old,
                        client=client,
                        processed_ids=processed_ids,
                    )
                    site_errors = (df.attrs or {}).get("errors") or {}
                    for err_site, err_msg in site_errors.items():
                        emit(f"    ⚠️ [{err_site}] Сообщение: {err_msg}")

                    if not df.empty:
                        emit(f"    ↳ Найдено вакансий: {len(df)}")
                        frames.append(df)
                    else:
                        emit(f"    ↳ По фильтру '{fname}' новых вакансий не найдено.")
            except Exception as e:
                emit(f"  ⚠️ [hirify] Ошибка при сборе по фильтрам: {e}")
    else:
        prev_had_rate_limit = False
        known_ids_in_run = set(processed_ids)
        for idx, term in enumerate(terms):
            if cancel_event and cancel_event.is_set():
                emit("⏹️ Поиск остановлен пользователем.")
                break
            if idx > 0:
                if site == "linkedin":
                    delay = random.uniform(10.0, 14.0) if prev_had_rate_limit else random.uniform(3.5, 6.0)
                    emit(f"⏳ [linkedin] Пауза {delay:.1f}с перед следующим запросом '{term}'...")
                    if cancel_event and cancel_event.wait(delay):
                        emit("⏹️ Поиск остановлен пользователем.")
                        break
                    if not cancel_event:
                        time.sleep(delay)
                else:
                    time.sleep(random.uniform(2.0, 4.0))

            try:
                if site in ("indeed", "glassdoor"):
                    eff_country = normalize_indeed_country(country_indeed, location)
                    emit(
                        f"🔍 Поиск [{site}] '{term}' на сервере-витрине '{eff_country}' [100% Remote] (за последние {hours_old}ч){easy_label}..."
                    )
                else:
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
                    hirify_mode=hirify_mode,
                    hirify_feed_id=hirify_feed_id,
                    processed_ids=known_ids_in_run,
                )

                prev_had_rate_limit = bool((df.attrs or {}).get("had_rate_limit"))
                site_errors = (df.attrs or {}).get("errors") or {}
                for err_site, err_msg in site_errors.items():
                    emit(f"  ⚠️ [{err_site}] Сообщение провайдера: {err_msg}")

                if not df.empty:
                    if "id" in df.columns:
                        known_ids_in_run.update(df["id"].dropna().astype(str).tolist())
                    emit(f"  ↳ [{site}] Найдено по '{term}': {len(df)}")
                    frames.append(df)
                else:
                    emit(f"  ↳ [{site}] По '{term}' вакансий не найдено.")
            except Exception as e:
                emit(f"  ⚠️ [{site}] Ошибка поиска для '{term}': {e}")

    new_matches_count = 0
    if frames:
        jobs = pd.concat(frames, ignore_index=True)
        total_raw = len(jobs)

        jobs = jobs.drop_duplicates(subset=["id"]).copy()
        after_id_dedup = len(jobs)
        jobs["_dedup_key"] = (
            jobs["title"].fillna("").str.strip().str.lower()
            + "::"
            + jobs["company"].fillna("").str.strip().str.lower()
        )
        jobs = jobs.drop_duplicates(subset=["_dedup_key"]).drop(columns=["_dedup_key"]).copy()
        unique_total = len(jobs)
        dup_id_count = total_raw - after_id_dedup
        dup_title_comp_count = after_id_dedup - unique_total
        dup_total = total_raw - unique_total

        if dup_total > 0:
            emit(
                f"📦 Суммарно карточек со всех запросов: {total_raw} "
                f"→ уникальных: {unique_total} (убрано дублей: {dup_total} — "
                f"по ID между запросами: {dup_id_count}, мульти-локации Title+Company: {dup_title_comp_count})"
            )
        else:
            emit(f"📦 Суммарно карточек со всех запросов: {total_raw}")

        new_jobs_mask = ~jobs["id"].astype(str).isin(processed_ids)
        unseen_jobs = jobs[new_jobs_mask].copy()
        skipped_seen = len(jobs) - len(unseen_jobs)
        if skipped_seen:
            emit(f"⏭️ Пропущено уже обработанных ранее вакансий (из БД по ID): {skipped_seen}")

        # Кросс-системная дедупликация по Title+Company против уже сохранённых в БД вакансий
        if not unseen_jobs.empty:
            db_tc_keys = jobs_repo.get_processed_title_company_keys(conn)
            if db_tc_keys:
                tc_series = (
                    unseen_jobs["title"].fillna("").str.strip().str.lower()
                    + "::"
                    + unseen_jobs["company"].fillna("").str.strip().str.lower()
                )
                cross_dup_mask = tc_series.isin(db_tc_keys)
                cross_dups = int(cross_dup_mask.sum())
                if cross_dups > 0:
                    emit(f"⏭️ Пропущено кросс-борд дублей (Title+Company уже есть в БД): {cross_dups}")
                    unseen_jobs = unseen_jobs[~cross_dup_mask].copy()

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
                if cancel_event and cancel_event.is_set():
                    emit("⏹️ Загрузка карточек остановлена пользователем.")
                    break
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
                    details = fetch_job_details(session, job_id, on_retry=emit)
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

    # Фиксируем время успешной проверки источника, если пайплайн не был прерван
    if not (cancel_event and cancel_event.is_set()):
        total_fetched_cards = sum(len(f) for f in frames) if frames else 0
        loc_display = "feeds" if (site == "hirify" and hirify_mode == "feeds") else (location if site in ("linkedin", "hirify") else country_indeed)
        record_provider_check(
            conn,
            site=site,
            location=loc_display,
            hours_old=hours_old,
            fetched_count=total_fetched_cards,
            matched_count=new_matches_count,
        )

    if run_llm_enrichment:
        if cancel_event and cancel_event.is_set():
            emit("⏹️ Пайплайн остановлен до запуска LLM.")
        elif new_matches_count > 0:
            enrich_and_score_pending_jobs(
                conn,
                model=llm_model,
                limit=llm_limit,
                on_progress=on_progress,
                cancel_event=cancel_event,
            )
        else:
            emit("⏭️ Новых кандидатов для ИИ-оценки не появилось — запуск LLM пропущен.")

    results = jobs_repo.list_final_matches(conn, min_score=config.FAIR_SCORE_THRESHOLD)
    conn.close()
    return results


PROVIDER_CHECKS_META_KEY = "provider_check_timestamps_v1"
MACRO_SETTINGS_META_KEY = "macro_pipeline_settings_v1"
ALL_PROVIDERS = ("linkedin", "hirify", "indeed", "glassdoor")

DEFAULT_MACRO_SETTINGS: dict[str, Any] = {
    "execution_mode": "per_provider",  # "per_provider" | "batch_all_then_llm"
    "hours_mode": "auto_from_last_run",  # "auto_from_last_run" | "fixed"
    "default_hours_old": 12,
    "max_auto_hours_old": 48,
    "results_wanted": 50,
    "llm_limit": 50,
    "steps": [
        {
            "site": "hirify",
            "enabled": True,
            "hirify_mode": "feeds",
            "hirify_feed_id": "all_active",
            "locations": ["Worldwide"],
            "easy_apply": False,
        },
        {
            "site": "linkedin",
            "enabled": True,
            "locations": ["EMEA", "Worldwide"],
            "easy_apply": False,
        },
        {
            "site": "indeed",
            "enabled": True,
            "locations": ["uk", "germany", "netherlands"],
            "easy_apply": False,
        },
        {
            "site": "glassdoor",
            "enabled": False,
            "locations": ["uk", "germany"],
            "easy_apply": False,
        },
    ],
}


def record_provider_check(
    conn: sqlite3.Connection,
    site: str,
    location: str | None = None,
    hours_old: int = 4,
    hours_old_used: int | None = None,
    fetched_count: int = 0,
    matched_count: int = 0,
) -> None:
    site_key = (site or "linkedin").strip().lower()
    eff_hours = hours_old_used if hours_old_used is not None else hours_old
    current = jobs_repo.get_app_metadata_json(conn, PROVIDER_CHECKS_META_KEY) or {}
    current[site_key] = {
        "last_checked_at": datetime.now(timezone.utc).isoformat(),
        "last_location": location,
        "last_hours_old": eff_hours,
        "last_fetched_count": fetched_count,
        "last_matched_count": matched_count,
    }
    jobs_repo.set_app_metadata_json(conn, PROVIDER_CHECKS_META_KEY, current)


def get_provider_check_status(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    stored = jobs_repo.get_app_metadata_json(conn, PROVIDER_CHECKS_META_KEY) or {}
    fallback_by_site = jobs_repo.get_last_processed_at_by_site(conn)
    macro_cfg = get_macro_settings(conn)
    default_hours = int(macro_cfg.get("default_hours_old") or 12)
    max_auto_hours = int(macro_cfg.get("max_auto_hours_old") or 48)

    now_utc = datetime.now(timezone.utc)
    result: dict[str, dict[str, Any]] = {}

    for site in ALL_PROVIDERS:
        info = dict(stored.get(site) or {})
        last_ts = info.get("last_checked_at") or fallback_by_site.get(site)
        hours_since: float | None = None
        recommended_hours = default_hours

        if last_ts:
            try:
                dt = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                delta_sec = max(0.0, (now_utc - dt).total_seconds())
                hours_since = round(delta_sec / 3600.0, 1)
                recommended_hours = min(max(1, math.ceil(delta_sec / 3600.0) + 1), max_auto_hours)
            except Exception:
                last_ts = None

        result[site] = {
            "site": site,
            "last_checked_at": last_ts,
            "hours_since": hours_since,
            "hours_since_last_check": hours_since,
            "recommended_hours_old": recommended_hours,
            "last_location": info.get("last_location"),
            "last_hours_old": info.get("last_hours_old"),
            "fetched_count": info.get("last_fetched_count"),
            "matched_count": info.get("last_matched_count"),
            "last_fetched_count": info.get("last_fetched_count"),
            "last_matched_count": info.get("last_matched_count"),
        }
    return result


def get_macro_settings(conn: sqlite3.Connection) -> dict[str, Any]:
    stored = jobs_repo.get_app_metadata_json(conn, MACRO_SETTINGS_META_KEY)
    if not stored:
        return json_clone_macro_defaults()

    merged = json_clone_macro_defaults()
    for k in ("execution_mode", "hours_mode", "default_hours_old", "max_auto_hours_old", "results_wanted", "llm_limit"):
        if k in stored and stored[k] is not None:
            merged[k] = stored[k]

    if isinstance(stored.get("steps"), list) and stored["steps"]:
        steps_by_site = {s.get("site"): s for s in stored["steps"] if isinstance(s, dict) and s.get("site")}
        new_steps = []
        for def_step in merged["steps"]:
            s_name = def_step["site"]
            if s_name in steps_by_site:
                upd = {**def_step, **steps_by_site[s_name]}
                if s_name in ("indeed", "glassdoor"):
                    raw_countries = upd.get("countries") or upd.get("locations") or def_step["locations"]
                    countries = [normalize_indeed_country(c, c) for c in raw_countries if c]
                    upd["countries"] = countries
                    upd["locations"] = countries
                else:
                    locs = upd.get("locations") or def_step["locations"]
                    upd["locations"] = locs
                new_steps.append(upd)
            else:
                disabled_step = {**def_step, "enabled": False}
                new_steps.append(disabled_step)
        merged["steps"] = new_steps
    return merged


def json_clone_macro_defaults() -> dict[str, Any]:
    import copy
    return copy.deepcopy(DEFAULT_MACRO_SETTINGS)


def save_macro_settings(conn: sqlite3.Connection, settings: dict[str, Any]) -> dict[str, Any]:
    current = get_macro_settings(conn)
    for k in ("execution_mode", "hours_mode", "default_hours_old", "max_auto_hours_old", "results_wanted", "llm_limit"):
        if k in settings and settings[k] is not None:
            current[k] = settings[k]
    if isinstance(settings.get("steps"), list) and settings["steps"]:
        current["steps"] = settings["steps"]
    jobs_repo.set_app_metadata_json(conn, MACRO_SETTINGS_META_KEY, current)
    return get_macro_settings(conn)


def run_macro_pipeline(
    settings_override: dict[str, Any] | None = None,
    search_terms: str | list[str] = config.DEFAULT_SEARCH_TERMS,
    llm_model: str = config.DEFAULT_MODEL,
    on_progress: Callable[[str], None] | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """
    Макро-обход всех включённых в настройках систем (Hirify, LinkedIn, Indeed, Glassdoor)
    с автоматическим расчётом окна времени hours_old от последней проверки каждого источника.
    """
    def emit(msg: str) -> None:
        logger.info("%s", msg)
        if on_progress:
            on_progress(msg)

    conn = connect()
    try:
        macro_cfg = save_macro_settings(conn, settings_override) if settings_override else get_macro_settings(conn)
        check_status = get_provider_check_status(conn)
    finally:
        conn.close()

    exec_mode = macro_cfg.get("execution_mode", "per_provider")
    hours_mode = macro_cfg.get("hours_mode", "auto_from_last_run")
    default_hours = int(macro_cfg.get("default_hours_old") or 12)
    max_auto_hours = int(macro_cfg.get("max_auto_hours_old") or 48)
    results_wanted = int(macro_cfg.get("results_wanted") or 50)
    llm_limit = int(macro_cfg.get("llm_limit") or 50)
    steps = [s for s in (macro_cfg.get("steps") or []) if s.get("enabled")]

    mode_label = (
        "По очереди по системам (Сбор → ИИ → Скоринг)"
        if exec_mode == "per_provider"
        else "Сначала сбор всех карточек со всех систем → Единый ИИ-разбор в конце"
    )
    emit(f"⚡ Старт МАКРО-ОБХОДА ({len(steps)} систем) | Режим: {mode_label}")

    run_llm_each = exec_mode == "per_provider"
    completed_steps = 0

    for step_idx, step in enumerate(steps, start=1):
        if cancel_event and cancel_event.is_set():
            emit("⏹️ Макро-обход остановлен пользователем.")
            break

        site = (step.get("site") or "linkedin").strip().lower()
        p_info = check_status.get(site) or {}
        hours_since = p_info.get("hours_since_last_check")

        if hours_mode == "auto_from_last_run" and hours_since is not None:
            effective_hours = min(max(1, math.ceil(hours_since) + 1), max_auto_hours)
            emit(
                f"🚀 === Шаг [{step_idx}/{len(steps)}]: {site.upper()} "
                f"(последняя проверка {hours_since}ч назад → авто-окно {effective_hours}ч) ==="
            )
        else:
            effective_hours = default_hours
            reason_str = "первый запуск" if hours_since is None else "фиксированный режим"
            emit(
                f"🚀 === Шаг [{step_idx}/{len(steps)}]: {site.upper()} "
                f"({reason_str} → окно {effective_hours}ч) ==="
            )

        easy_apply = True if step.get("easy_apply") else None
        hirify_mode = step.get("hirify_mode") or "feeds"
        hirify_feed_id = step.get("hirify_feed_id")
        if site in ("indeed", "glassdoor"):
            locations = step.get("countries") or step.get("locations") or ["uk"]
        else:
            locations = step.get("locations") or ["EMEA"]

        if site == "hirify" and hirify_mode == "feeds":
            fetch_and_filter_jobs(
                search_terms=search_terms,
                site_names=["hirify"],
                location="Worldwide",
                results_wanted=results_wanted,
                hours_old=effective_hours,
                run_llm_enrichment=run_llm_each,
                llm_model=llm_model,
                llm_limit=llm_limit,
                on_progress=on_progress,
                hirify_mode="feeds",
                hirify_feed_id=hirify_feed_id,
                cancel_event=cancel_event,
            )
        else:
            for loc_idx, loc in enumerate(locations, start=1):
                if cancel_event and cancel_event.is_set():
                    break
                eff_loc = normalize_indeed_country(loc, loc) if site in ("indeed", "glassdoor") else loc
                if loc_idx > 1:
                    emit(f"⏳ [{site}] Переход к следующей локации '{eff_loc}' ({loc_idx}/{len(locations)})...")
                fetch_and_filter_jobs(
                    search_terms=search_terms,
                    site_names=[site],
                    location=eff_loc,
                    country_indeed=eff_loc if site in ("indeed", "glassdoor") else "uk",
                    results_wanted=results_wanted,
                    hours_old=effective_hours,
                    easy_apply=easy_apply,
                    run_llm_enrichment=run_llm_each,
                    llm_model=llm_model,
                    llm_limit=llm_limit,
                    on_progress=on_progress,
                    hirify_mode=hirify_mode,
                    hirify_feed_id=hirify_feed_id,
                    cancel_event=cancel_event,
                )
        completed_steps += 1

    if exec_mode == "batch_all_then_llm" and not (cancel_event and cancel_event.is_set()):
        emit("🧠 === Финальный этап макроса: единый ИИ-разбор и скоринг всех собранных карточек ===")
        conn = connect()
        try:
            enrich_and_score_pending_jobs(
                conn,
                model=llm_model,
                limit=llm_limit,
                on_progress=on_progress,
                cancel_event=cancel_event,
            )
        finally:
            conn.close()

    emit(f"🏁 Макро-обход завершён (выполнено систем: {completed_steps}/{len(steps)})!")
    return {
        "completed_steps": completed_steps,
        "steps_executed": completed_steps,
        "total_steps": len(steps),
        "execution_mode": exec_mode,
    }

