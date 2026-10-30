"""Точка входа CLI и обратная совместимость функций ядра.

Основная реализация перенесена в пакет `job_filter`:
- База данных и схема: `job_filter.db`
- Репозитории: `job_filter.repositories`
- Сервисы: `job_filter.services`
- Скрапинг: `job_filter.scraping`
- Скоринг: `job_filter.scoring`
"""
from job_filter.config import DB_PATH, DEFAULT_MODEL
from job_filter.db.connection import connect as _connect, init_db as _init_db_func
from job_filter.repositories import candidate_repo, jobs_repo, skills_repo
from job_filter.scraping.linkedin import extract_linkedin_apply_url, fetch_job_details
from job_filter.services import blacklist_service, skills_service
from job_filter.services.pipeline import (
    _save_processed_job,
    enrich_and_score_pending_jobs,
    fetch_and_filter_jobs,
)
from job_filter.utils.urls import (
    extract_root_domain,
    match_blacklisted_domain as _match_blacklisted_domain,
    normalize_company_key,
)


def init_db(db_path=DB_PATH):
    _init_db_func(db_path)
    return _connect(db_path)


def get_candidate_settings(conn):
    return candidate_repo.get_settings(conn)


def save_candidate_settings(conn, profile_text: str, cv_text: str):
    return candidate_repo.save_settings(conn, profile_text, cv_text)


def get_skill_matrix_data(conn):
    return skills_repo.get_matrix(conn)


def save_skill_category(conn, category_id: str, title: str, multiplier: float = 2.0, max_points: int = 30, sort_order: int = 0):
    return skills_service.save_category(conn, category_id, title, multiplier, max_points, sort_order)


def delete_skill_category(conn, category_id: str):
    skills_service.delete_category(conn, category_id)


def save_candidate_skill(conn, skill_id: str, category_id: str, name: str, years_experience: float = 0.0, weight_points: int | None = None, is_primary: bool = False, aliases: list[str] | None = None):
    return skills_service.save_skill(conn, skill_id, category_id, name, years_experience, weight_points, is_primary, aliases)


def delete_candidate_skill(conn, skill_id: str):
    skills_service.delete_skill(conn, skill_id)


def match_blacklisted_domain(conn, url_or_domain: str | None):
    return blacklist_service.match_blacklisted_domain(conn, url_or_domain)


def get_blacklist_data(conn):
    return blacklist_service.get_blacklist_data(conn)


def add_blacklisted_board(conn, domain_or_url: str | None = None, company: str | None = None, job_id: str | None = None, reason: str = "Невозможно заполнить форму (в чёрном списке)", hide_job: bool = True):
    return blacklist_service.add_blacklisted_board(conn, domain_or_url, company, job_id, reason, hide_job)


def remove_blacklisted_board(conn, domain: str):
    blacklist_service.remove_blacklisted_board(conn, domain)


def remove_company_ats_map(conn, company_key: str):
    blacklist_service.remove_company_ats_map(conn, company_key)


def get_processed_ids(conn):
    return jobs_repo.get_processed_ids(conn)


def mark_job_processed(conn, job_id: str, title: str, company: str, url: str, date_posted: str, matched: bool, site: str = "linkedin", location: str | None = None, is_remote: bool | None = None, reject_reason: str | None = None, seniority_level: str | None = None, employment_type: str | None = None, job_function: str | None = None, industry: str | None = None, salary: str | None = None, description: str | None = None, enrichment_json: str | None = None, score: int | None = None, tier: str | None = None, score_details_json: str | None = None, apply_url: str | None = None, ats_domain: str | None = None):
    _save_processed_job(
        conn,
        job_id=job_id,
        title=title,
        company=company,
        url=url,
        date_posted=date_posted,
        matched=matched,
        site=site,
        location=location,
        is_remote=is_remote,
        reject_reason=reject_reason,
        seniority_level=seniority_level,
        employment_type=employment_type,
        job_function=job_function,
        industry=industry,
        salary=salary,
        description=description,
        apply_url=apply_url,
        ats_domain=ats_domain,
    )


def update_job_enrichment_and_score(conn, job_id: str, enrichment, score_res):
    matched = 0 if (not score_res.geo_passed or score_res.score < 50) else 1
    reject_reason = score_res.geo_reject_reason if not score_res.geo_passed else (f"low_score:{score_res.score}" if score_res.score < 50 else None)
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


if __name__ == "__main__":
    matched = fetch_and_filter_jobs()
    print(f"\n🎯 Итого вакансий в сухом остатке (Score >= 50): {len(matched)}\n")
    for job in matched:
        print(f"🔥 [{job.get('score')}/100 | {job.get('tier')}] {job['title']} @ {job['company']} ({job['date_posted']})")
        print(f"🔗 {job['url']}\n")
