"""Роуты чёрного списка нежелательных ATS-бордов и проверки URL из браузерного расширения."""
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query

from job_filter.api.deps import get_db
from job_filter.api.schemas import AddBlacklistRequest
from job_filter.services import blacklist_service
from job_filter.utils.urls import is_search_aggregator_domain, is_utility_or_captcha_domain

router = APIRouter(prefix="/api/blacklist", tags=["blacklist"])


@router.get("")
def read_blacklist(conn: sqlite3.Connection = Depends(get_db)):
    data = blacklist_service.get_blacklist_data(conn)
    data["last_opened_job"] = blacklist_service.last_opened_tracker.get()
    return data


@router.get("/check")
def check_url_in_blacklist(
    url: str = Query("", description="Текущий URL вкладки"),
    frames: str = Query("", description="Через запятую URL всех iframe на странице"),
    auto_link: bool = Query(True, description="Автоматически привязать обнаруженный говносайт к последней открытой вакансии"),
    conn: sqlite3.Connection = Depends(get_db),
):
    return blacklist_service.check_url(conn, url=url, frames=frames, auto_link=auto_link)


@router.post("")
def create_blacklist_entry(
    body: AddBlacklistRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    if body.domain_or_url and is_search_aggregator_domain(body.domain_or_url):
        raise HTTPException(
            status_code=400,
            detail="Нельзя заблокировать поисковый агрегатор (LinkedIn, Hirify, Indeed, Glassdoor). Добавьте компанию в чёрный список или укажите сайт ATS.",
        )
    if body.domain_or_url and is_utility_or_captcha_domain(body.domain_or_url):
        raise HTTPException(
            status_code=400,
            detail="Нельзя заблокировать служебный сервис капчи/трекинга.",
        )

    job_id = body.job_id
    company = body.company

    last_op = blacklist_service.last_opened_tracker.get()
    if body.use_last_opened and blacklist_service.last_opened_tracker.is_recent():
        if not job_id and last_op.get("job_id"):
            job_id = str(last_op["job_id"])
        if not company and last_op.get("company"):
            company = str(last_op["company"])

    res = blacklist_service.add_blacklisted_board(
        conn,
        domain_or_url=body.domain_or_url,
        company=company,
        job_id=job_id,
        reason=body.reason,
        hide_job=body.hide_job,
    )
    data = blacklist_service.get_blacklist_data(conn)
    return {"added": res, **data}


@router.delete("/domain/{domain:path}")
def delete_blacklisted_domain(
    domain: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    blacklist_service.remove_blacklisted_board(conn, domain)
    return blacklist_service.get_blacklist_data(conn)


@router.delete("/company/{company_key:path}")
def delete_company_ats_entry(
    company_key: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    blacklist_service.remove_company_ats_map(conn, company_key)
    return blacklist_service.get_blacklist_data(conn)

