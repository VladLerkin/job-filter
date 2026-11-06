"""Роуты работы со списком вакансий, статусами и пересчётом скоров."""
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query

from job_filter.api.deps import get_db
from job_filter.api.schemas import UpdateStatusRequest
from job_filter.services import jobs_service, skills_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
def list_jobs(
    tab: str = Query("top", description="top | good | fair | pending | applied | rejected | actionable"),
    conn: sqlite3.Connection = Depends(get_db),
):
    return jobs_service.list_jobs(conn, tab=tab)


@router.post("/rescore")
def rescore_all_enriched_jobs(conn: sqlite3.Connection = Depends(get_db)):
    updated = skills_service.rescore_all_jobs(conn)
    return {"rescored": updated}


@router.patch("/{job_id}/status")
def update_job_status(
    job_id: str,
    body: UpdateStatusRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = jobs_service.update_status(
        conn,
        job_id,
        body.user_status,
        user_reject_reason=body.user_reject_reason,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "user_status": body.user_status,
        "user_reject_reason": body.user_reject_reason,
    }


@router.get("/user-rejections")
def list_user_rejections(conn: sqlite3.Connection = Depends(get_db)):
    """Возвращает список отклоненных пользователем вакансий с причинами для обучения."""
    return jobs_service.get_user_rejections(conn)


@router.post("/{job_id}/opened")
def record_job_opened(
    job_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    last_op = jobs_service.record_opened(conn, job_id)
    if not last_op:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "ok", "last_opened_job": last_op}


@router.get("/last-opened")
def get_last_opened_job():
    from job_filter.services.blacklist_service import last_opened_tracker
    return {"last_opened_job": last_opened_tracker.get()}

