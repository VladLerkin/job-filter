"""Сервис работы со списком вакансий: агрегация статистики, фильтрация по вкладкам, ATS-метки и сортировка."""
import json
import logging
import sqlite3

from job_filter.repositories import blacklist_repo, jobs_repo
from job_filter.services.blacklist_service import last_opened_tracker
from job_filter.utils.urls import (
    ATS_DOMAIN_ALIASES,
    extract_root_domain,
    find_domain_in_map,
    normalize_company_key,
)

logger = logging.getLogger(__name__)


def list_jobs(conn: sqlite3.Connection, tab: str = "actionable") -> dict:
    rows = jobs_repo.list_all(conn)
    bad_rows = blacklist_repo.list_boards(conn)
    comp_rows = blacklist_repo.list_companies(conn)

    bad_map = {r["domain"].lower(): (r["reason"] or "В чёрном списке / форма не заполняется") for r in bad_rows}
    for src, dst in ATS_DOMAIN_ALIASES.items():
        if src in bad_map and dst not in bad_map:
            bad_map[dst] = bad_map[src]

    comp_ats_map = {r["company_key"]: r["ats_domain"] for r in comp_rows}

    stats = {
        "total_in_db": len(rows),
        "top_match": 0,
        "good_match": 0,
        "pending_llm": 0,
        "applied": 0,
        "rejected": 0,
        "bad_boards_count": len(bad_rows),
    }

    items = []
    for r in rows:
        d = dict(r)
        enrichment = None
        score_details = None
        if d.get("enrichment_json"):
            try:
                enrichment = json.loads(d["enrichment_json"])
            except Exception:
                enrichment = None
        if d.get("score_details_json"):
            try:
                score_details = json.loads(d["score_details_json"])
            except Exception:
                score_details = None

        d["enrichment"] = enrichment
        d["score_details"] = score_details
        d.pop("enrichment_json", None)
        d.pop("score_details_json", None)

        comp_key = normalize_company_key(d.get("company"))
        ats_dom = (
            d.get("ats_domain")
            or extract_root_domain(d.get("apply_url"))
            or comp_ats_map.get(comp_key)
        )
        d["ats_domain"] = ats_dom

        bad_reason = None
        if ats_dom:
            matched_key = find_domain_in_map(ats_dom, bad_map)
            if matched_key:
                bad_reason = bad_map[matched_key]
        if not bad_reason and comp_key and f"company:{comp_key}" in bad_map:
            bad_reason = bad_map[f"company:{comp_key}"]
            if not d["ats_domain"]:
                d["ats_domain"] = f"company:{comp_key}"

        d["is_bad_board"] = bad_reason is not None
        d["bad_board_reason"] = bad_reason

        u_status = d.get("user_status") or "new"
        score = d.get("score")
        has_desc = bool(d.get("description"))
        reject_reason = d.get("reject_reason")

        # Подсчет статистики
        if u_status == "applied":
            stats["applied"] += 1
        elif u_status == "hidden":
            stats["rejected"] += 1
        elif score is not None:
            if d.get("matched") == 1 and score >= 70:
                stats["top_match"] += 1
            elif d.get("matched") == 1 and 50 <= score < 70:
                stats["good_match"] += 1
            else:
                stats["rejected"] += 1
        elif has_desc and not reject_reason:
            stats["pending_llm"] += 1
        else:
            stats["rejected"] += 1

        # Фильтрация по выбранной вкладке
        if tab == "applied":
            if u_status == "applied":
                items.append(d)
        elif tab == "pending":
            if score is None and has_desc and not reject_reason and u_status != "hidden":
                items.append(d)
        elif tab == "rejected":
            if u_status == "hidden" or (score is not None and (score < 50 or d.get("matched") == 0)) or reject_reason:
                items.append(d)
        elif tab == "top":
            if u_status not in ("applied", "hidden") and d.get("matched") == 1 and score is not None and score >= 70:
                items.append(d)
        elif tab == "good":
            if u_status not in ("applied", "hidden") and d.get("matched") == 1 and score is not None and 50 <= score < 70:
                items.append(d)
        else:  # actionable (top + good)
            if u_status not in ("applied", "hidden") and d.get("matched") == 1 and score is not None and score >= 50:
                items.append(d)

    def sort_key(item: dict):
        not_bad_board = 0 if item.get("is_bad_board") else 1
        sd = item.get("score_details") or {}
        clean_title = 1 if sd.get("has_clean_title", True) else 0
        sc = item.get("score") if item.get("score") is not None else -1
        dt = item.get("date_posted") or ""
        return (not_bad_board, clean_title, sc, dt)

    items.sort(key=sort_key, reverse=True)
    return {"stats": stats, "jobs": items, "last_opened_job": last_opened_tracker.get()}


def update_status(conn: sqlite3.Connection, job_id: str, status: str) -> bool:
    updated = jobs_repo.set_user_status(conn, job_id, status)
    conn.commit()
    return updated > 0


def record_opened(conn: sqlite3.Connection, job_id: str) -> dict | None:
    job = jobs_repo.get_job(conn, job_id)
    if not job:
        return None
    return last_opened_tracker.record(
        job_id=job["job_id"],
        title=job.get("title"),
        company=job.get("company"),
        url=job.get("url"),
    )

