"""Сервис работы со списком вакансий: агрегация статистики, фильтрация по вкладкам, ATS-метки и сортировка."""
import json
import logging
import sqlite3

from job_filter import config
from job_filter.repositories import blacklist_repo, jobs_repo
from job_filter.services.blacklist_service import last_opened_tracker
from job_filter.utils.urls import (
    ATS_DOMAIN_ALIASES,
    extract_root_domain,
    find_domain_in_map,
    normalize_company_key,
)

logger = logging.getLogger(__name__)


def parse_auto_reject(reject_reason: str | None, score: int | None) -> tuple[str, str]:
    rr = (reject_reason or "").strip()
    if "single_country_lock:" in rr:
        target = rr.split(":", 1)[1]
        return "location", f"Ограничение по стране: {target}"
    elif "country_pool_lock:" in rr:
        targets = rr.split(":", 1)[1]
        return "location", f"Закрытый пул стран: {targets}"
    elif "onsite_abroad_lock:" in rr:
        target = rr.split(":", 1)[1]
        return "location", f"Офис / Гибрид за рубежом: {target}"
    elif "geo_ineligible:" in rr:
        target = rr.split(":", 1)[1]
        return "location", f"Недоступна локация: {target}"
    elif rr == "business_travel_required" or "business_travel:" in rr:
        return "location", "Требуются регулярные командировки / выезды"
    elif rr == "us_only_lock":
        return "location", "Только США (US only)"
    elif rr == "ru_only_lock":
        return "location", "Только РФ / RU"
    elif "low_score" in rr or (score is not None and score < config.FAIR_SCORE_THRESHOLD):
        sc = score if score is not None else (rr.split(":", 1)[1] if ":" in rr else "?")
        return "low_score", f"Низкий скор ИИ: {sc}/100"
    elif rr == "missing_keywords":
        return "missing_keywords", "Отсутствуют ключевые слова в описании"
    elif rr == "excluded_title":
        return "excluded_title", "Неподходящая должность / профиль"
    elif "excluded_seniority:" in rr:
        level = rr.split(":", 1)[1]
        return "seniority", f"Неподходящий грейд: {level}"
    elif "required_language:" in rr:
        lang = rr.split(":", 1)[1]
        return "language", f"Требуется язык: {lang}"
    elif "excluded_industry:" in rr:
        ind = rr.split(":", 1)[1]
        return "industry", f"Исключенная отрасль: {ind}"
    elif "bad_board:" in rr:
        bb = rr.split(":", 1)[1]
        return "bad_board", f"Чёрный список ATS: {bb}"
    elif "contract_lock:" in rr:
        c = rr.split(":", 1)[1]
        return "contract", f"Формат контракта: {c}"
    elif rr:
        return "other", f"Фильтр: {rr}"
    else:
        return "unmatched", "Не соответствует критериям отбора"


def list_jobs(conn: sqlite3.Connection, tab: str = "actionable") -> dict:
    rows = jobs_repo.list_all(conn, include_description=False)
    bad_rows = blacklist_repo.list_boards(conn)
    comp_rows = blacklist_repo.list_companies(conn)

    bad_map = {r["domain"].lower(): (r["reason"] or "В чёрном списке / форма не заполняется") for r in bad_rows}
    for src, dst in ATS_DOMAIN_ALIASES.items():
        if src in bad_map and dst not in bad_map:
            bad_map[dst] = bad_map[src]

    comp_ats_map = {r["company_key"]: r["ats_domain"] for r in comp_rows}

    top_thr = config.TOP_SCORE_THRESHOLD
    good_thr = config.GOOD_SCORE_THRESHOLD
    fair_thr = config.FAIR_SCORE_THRESHOLD

    stats = {
        "total_in_db": len(rows),
        "top_match": 0,
        "good_match": 0,
        "fair_match": 0,
        "actionable": 0,
        "pending_llm": 0,
        "applied": 0,
        "applied_waiting": 0,
        "applied_confirmed": 0,
        "applied_interview": 0,
        "applied_rejected": 0,
        "rejected": 0,
        "rejected_user": 0,
        "rejected_auto": 0,
        "bad_boards_count": len(bad_rows),
    }

    items = []
    for r in rows:
        d = dict(r)
        u_status = d.get("user_status") or "new"
        score = d.get("score")
        has_desc = bool(d.get("has_description") or d.get("description"))
        d["has_description"] = has_desc
        reject_reason = d.get("reject_reason")

        # Определение источника и категории отсева
        is_user_rejected = u_status in ("hidden", "rejected")
        is_auto_rejected = (u_status != "saved") and (
            (score is not None and (score < fair_thr or d.get("matched") == 0)) or bool(reject_reason)
        )
        is_rejected = is_user_rejected or is_auto_rejected

        # Подсчет статистики
        if u_status == "applied":
            stats["applied"] += 1
            app_stage = d.get("application_stage") or "applied"
            d["application_stage"] = app_stage
            if app_stage == "confirmed":
                stats["applied_confirmed"] += 1
            elif app_stage == "interview":
                stats["applied_interview"] += 1
            elif app_stage == "rejected_by_company":
                stats["applied_rejected"] += 1
            else:
                stats["applied_waiting"] += 1
        elif u_status == "saved":
            if score is not None and score >= top_thr:
                stats["top_match"] += 1
            elif score is not None and score >= good_thr:
                stats["good_match"] += 1
            else:
                stats["fair_match"] += 1
        elif is_user_rejected:
            stats["rejected"] += 1
            stats["rejected_user"] += 1
        elif score is not None:
            if d.get("matched") == 1 and score >= top_thr:
                stats["top_match"] += 1
            elif d.get("matched") == 1 and good_thr <= score < top_thr:
                stats["good_match"] += 1
            elif d.get("matched") == 1 and fair_thr <= score < good_thr:
                stats["fair_match"] += 1
            else:
                stats["rejected"] += 1
                stats["rejected_auto"] += 1
        elif has_desc and not reject_reason:
            stats["pending_llm"] += 1
        else:
            stats["rejected"] += 1
            stats["rejected_auto"] += 1

        # Фильтрация по выбранной вкладке
        in_tab = False
        if tab == "applied":
            in_tab = u_status == "applied"
        elif tab == "pending":
            in_tab = (
                score is None
                and has_desc
                and not reject_reason
                and u_status not in ("hidden", "rejected", "saved")
            )
        elif tab == "rejected":
            in_tab = is_rejected
        elif tab == "top":
            in_tab = (u_status == "saved" and score is not None and score >= top_thr) or (
                u_status not in ("applied", "hidden", "rejected", "saved")
                and d.get("matched") == 1
                and score is not None
                and score >= top_thr
            )
        elif tab == "good":
            in_tab = (u_status == "saved" and score is not None and good_thr <= score < top_thr) or (
                u_status not in ("applied", "hidden", "rejected", "saved")
                and d.get("matched") == 1
                and score is not None
                and good_thr <= score < top_thr
            )
        elif tab == "fair":
            in_tab = (u_status == "saved" and (score is None or score < good_thr)) or (
                u_status not in ("applied", "hidden", "rejected", "saved")
                and d.get("matched") == 1
                and score is not None
                and fair_thr <= score < good_thr
            )
        else:  # actionable (top + good + fair: score >= fair_thr)
            in_tab = u_status == "saved" or (
                u_status not in ("applied", "hidden", "rejected", "saved")
                and d.get("matched") == 1
                and score is not None
                and score >= fair_thr
            )

        if not in_tab:
            continue

        # Десериализация JSON и вычисление ATS-меток выполняются ТОЛЬКО для вакансий выбранной вкладки
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

        if is_user_rejected:
            d["rejection_source"] = "user"
            d["rejection_category"] = "user_manual" if u_status == "rejected" else "user_hidden"
            d["rejection_reason_display"] = d.get("user_reject_reason") or (
                "Скрыто в корзину" if u_status == "hidden" else "Без указания причины"
            )
        elif is_auto_rejected:
            d["rejection_source"] = "auto"
            cat, label = parse_auto_reject(reject_reason, score)
            d["rejection_category"] = cat
            d["rejection_reason_display"] = label
        else:
            d["rejection_source"] = None
            d["rejection_category"] = None
            d["rejection_reason_display"] = None

        items.append(d)

    stats["actionable"] = stats["top_match"] + stats["good_match"] + stats["fair_match"]

    def sort_key(item: dict):
        not_bad_board = 0 if item.get("is_bad_board") else 1
        sd = item.get("score_details") or {}
        clean_title = 1 if sd.get("has_clean_title", True) else 0
        sc = item.get("score") if item.get("score") is not None else -1
        dt = item.get("date_posted") or ""
        if tab == "applied":
            stage_order = {
                "interview": 3,
                "confirmed": 2,
                "applied": 1,
                "rejected_by_company": 0,
            }.get(item.get("application_stage") or "applied", 1)
            return (stage_order, not_bad_board, clean_title, sc, dt)
        return (not_bad_board, clean_title, sc, dt)

    items.sort(key=sort_key, reverse=True)
    return {"stats": stats, "jobs": items, "last_opened_job": last_opened_tracker.get()}


def get_description(conn: sqlite3.Connection, job_id: str) -> str | None:
    return jobs_repo.get_job_description(conn, job_id)


def update_status(
    conn: sqlite3.Connection,
    job_id: str,
    status: str,
    user_reject_reason: str | None = None,
) -> bool:
    updated = jobs_repo.set_user_status(conn, job_id, status, user_reject_reason=user_reject_reason)
    conn.commit()
    return updated > 0


def update_application_stage(
    conn: sqlite3.Connection,
    job_id: str,
    application_stage: str,
    company_reject_reason: str | None = None,
    application_email_url: str | None = None,
) -> bool:
    from job_filter.llm.application_tracker import build_gmail_search_url

    if not application_email_url and application_stage == "interview":
        job = jobs_repo.get_job(conn, job_id)
        if job:
            application_email_url = job.get("application_email_url") or build_gmail_search_url(job.get("company"))

    updated = jobs_repo.set_application_stage(
        conn,
        job_id=job_id,
        application_stage=application_stage,
        company_reject_reason=company_reject_reason,
        application_email_url=application_email_url,
    )
    conn.commit()
    return updated > 0


def get_tracker_prompt(
    conn: sqlite3.Connection,
    skill_name: str = "@job-application-tracker",
) -> dict:
    from job_filter.llm.application_tracker import build_gemini_tracker_prompt

    applied_jobs = jobs_repo.list_applied_jobs(conn)
    prompt = build_gemini_tracker_prompt(applied_jobs, skill_name=skill_name)
    unique_companies = len({(j.get("company") or "").strip() for j in applied_jobs if j.get("company")})
    return {
        "applied_count": len(applied_jobs),
        "companies_count": unique_companies,
        "skill_name": skill_name,
        "prompt": prompt,
    }


def sync_applied_tracker(
    conn: sqlite3.Connection,
    report_text: str | None = None,
    skill_name: str = "@job-application-tracker",
    apply_updates: bool = True,
) -> dict:
    from job_filter.llm.application_tracker import sync_tracker_with_llm

    applied_jobs = jobs_repo.list_applied_jobs(conn)
    result = sync_tracker_with_llm(
        applied_jobs=applied_jobs,
        report_text=report_text,
        skill_name=skill_name,
    )
    updates = result.get("updates") or []
    updated_count = 0
    if apply_updates and updates:
        for upd in updates:
            jid = upd.get("job_id")
            stage = upd.get("stage") or "applied"
            reason = upd.get("reason")
            email_url = upd.get("email_url")
            if jid:
                updated_count += jobs_repo.set_application_stage(
                    conn,
                    job_id=jid,
                    application_stage=stage,
                    company_reject_reason=reason,
                    application_email_url=email_url,
                )
        conn.commit()

    counts = {
        "confirmed": sum(1 for u in updates if u.get("stage") == "confirmed"),
        "interview": sum(1 for u in updates if u.get("stage") == "interview"),
        "rejected_by_company": sum(1 for u in updates if u.get("stage") == "rejected_by_company"),
    }
    return {
        "summary": result.get("summary") or "",
        "used_llm": result.get("used_llm", False),
        "applied_total": len(applied_jobs),
        "matched_count": len(updates),
        "updated_count": updated_count,
        "stage_counts": counts,
        "updates": updates,
    }


def get_user_rejections(conn: sqlite3.Connection) -> list[dict]:
    return jobs_repo.get_user_rejected_jobs(conn)


def record_opened(conn: sqlite3.Connection, job_id: str) -> dict | None:
    job = jobs_repo.get_job(conn, job_id)
    if not job:
        return None
    apply_url = job.get("apply_url")
    ats_domain = job.get("ats_domain") or extract_root_domain(apply_url)
    return last_opened_tracker.record(
        job_id=job["job_id"],
        title=job.get("title"),
        company=job.get("company"),
        url=job.get("url"),
        apply_url=apply_url,
        ats_domain=ats_domain,
    )

