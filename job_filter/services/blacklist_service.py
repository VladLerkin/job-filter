"""Сервис чёрного списка нежелательных ATS-бордов (говносайтов) и трекинга открытых вакансий."""
import logging
import sqlite3
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from job_filter import config
from job_filter.repositories import blacklist_repo, jobs_repo
from job_filter.utils.urls import (
    ATS_DOMAIN_ALIASES,
    extract_host,
    extract_root_domain,
    is_search_aggregator_domain,
    is_utility_or_captcha_domain,
    normalize_company_key,
)

logger = logging.getLogger(__name__)


class LastOpenedTracker:
    """Хранит информацию о последней вакансии, открытой пользователем в браузере."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: dict[str, str | float | None] = {
            "job_id": None,
            "title": None,
            "company": None,
            "url": None,
            "opened_ts": None,
            "opened_at": None,
        }

    def record(self, job_id: str, title: str | None, company: str | None, url: str | None) -> dict:
        with self._lock:
            self._state = {
                "job_id": job_id,
                "title": title,
                "company": company,
                "url": url,
                "opened_ts": time.time(),
                "opened_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            return dict(self._state)

    def get(self) -> dict:
        with self._lock:
            return dict(self._state)

    def is_recent(self, ttl_sec: int = config.LAST_OPENED_TTL_SEC) -> bool:
        with self._lock:
            ts = self._state.get("opened_ts")
            return isinstance(ts, (int, float)) and (time.time() - ts) < ttl_sec


last_opened_tracker = LastOpenedTracker()


def match_blacklisted_domain(
    conn: sqlite3.Connection,
    url_or_domain: str | None,
) -> dict[str, str] | None:
    """Проверяет, входит ли URL или домен в чёрный список."""
    if not url_or_domain:
        return None
    raw = url_or_domain.strip()
    if not raw or is_utility_or_captcha_domain(raw) or is_search_aggregator_domain(raw):
        return None
    host = extract_host(raw)
    root = extract_root_domain(host) or host

    bad_raw = blacklist_repo.get_board_reasons(conn)
    bad_map = {k: (v or "В черном списке") for k, v in bad_raw.items()}

    candidates = [host, root]
    if root in ATS_DOMAIN_ALIASES:
        candidates.append(ATS_DOMAIN_ALIASES[root])
    for alias_src, alias_dst in ATS_DOMAIN_ALIASES.items():
        if host.endswith("." + alias_src):
            candidates.append(alias_dst)

    for cand in candidates:
        if cand in bad_map:
            return {"domain": cand, "reason": bad_map[cand]}
    for bad_dom, rsn in bad_map.items():
        if host == bad_dom or host.endswith("." + bad_dom):
            return {"domain": bad_dom, "reason": rsn}
    return None


def get_blacklist_data(conn: sqlite3.Connection) -> dict:
    return {
        "boards": blacklist_repo.list_boards(conn),
        "companies": blacklist_repo.list_companies(conn),
    }


def add_blacklisted_board(
    conn: sqlite3.Connection,
    domain_or_url: str | None = None,
    company: str | None = None,
    job_id: str | None = None,
    reason: str = "Невозможно заполнить форму (в чёрном списке)",
    hide_job: bool = True,
) -> dict:
    now_iso = datetime.now(timezone.utc).isoformat()
    domain = extract_root_domain(domain_or_url) if domain_or_url else None
    if domain and is_utility_or_captcha_domain(domain):
        logger.warning("Попытка добавить в чёрный список служебный домен капчи/трекинга: %s (пропущено)", domain)
        domain = None
    elif domain and is_search_aggregator_domain(domain):
        logger.warning("Попытка добавить в чёрный список поисковый агрегатор: %s (пропущено)", domain)
        domain = None

    if job_id and not company:
        job = jobs_repo.get_job(conn, job_id)
        if job:
            company = job.get("company")
            if not domain:
                domain = job.get("ats_domain") or extract_root_domain(job.get("apply_url"))

    if not domain and company:
        domain = f"company:{normalize_company_key(company)}"

    if domain:
        blacklist_repo.upsert_board(conn, domain, reason, now_iso)
        if domain in ATS_DOMAIN_ALIASES:
            blacklist_repo.insert_board_if_absent(conn, ATS_DOMAIN_ALIASES[domain], reason, now_iso)

    comp_key = normalize_company_key(company)
    if comp_key and domain:
        blacklist_repo.upsert_company_ats(conn, comp_key, (company or "").strip(), domain, domain_or_url, now_iso)
        apply_val = domain_or_url if (domain_or_url and "://" in domain_or_url) else None
        jobs_repo.propagate_company_ats(conn, comp_key, domain, apply_val)

    if job_id:
        apply_val = domain_or_url if (domain_or_url and "://" in domain_or_url) else None
        hide_reason = f"bad_board:{domain or 'unknown'}" if hide_job else None
        jobs_repo.set_job_ats(conn, job_id, domain, apply_val, hide_with_reason=hide_reason)

    conn.commit()
    return {"domain": domain, "company": company, "job_id": job_id, "reason": reason}


def remove_blacklisted_board(conn: sqlite3.Connection, domain: str) -> None:
    blacklist_repo.delete_board(conn, domain)
    conn.commit()


def remove_company_ats_map(conn: sqlite3.Connection, company_key: str) -> None:
    blacklist_repo.delete_company_ats(conn, company_key)
    conn.commit()


def check_url(
    conn: sqlite3.Connection,
    url: str,
    frames: str,
    auto_link: bool = True,
) -> dict:
    all_urls = [
        u.strip() for u in ([url] + frames.split(","))
        if u.strip() and not is_utility_or_captcha_domain(u.strip()) and not is_search_aggregator_domain(u.strip())
    ]

    matched_info = None
    hit_url = None
    for u in all_urls:
        m = match_blacklisted_domain(conn, u)
        if m:
            matched_info = m
            hit_url = u
            break

    linked_job = None
    last_op = last_opened_tracker.get()
    is_recent = last_opened_tracker.is_recent()

    if matched_info and auto_link and is_recent and last_op.get("job_id"):
        add_blacklisted_board(
            conn,
            domain_or_url=hit_url or matched_info["domain"],
            company=str(last_op.get("company") or ""),
            job_id=str(last_op.get("job_id") or ""),
            reason=matched_info["reason"],
            hide_job=False,
        )
        linked_job = dict(last_op)

    boards = blacklist_repo.list_board_domains(conn)
    return {
        "is_blacklisted": matched_info is not None,
        "matched_domain": matched_info["domain"] if matched_info else None,
        "reason": matched_info["reason"] if matched_info else None,
        "hit_url": hit_url,
        "linked_job": linked_job,
        "last_opened_job": last_op if is_recent else None,
        "all_blacklisted_domains": boards,
    }

