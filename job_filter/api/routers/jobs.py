"""Роуты работы со списком вакансий, статусами и пересчётом скоров."""
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query

from job_filter.api.deps import get_db
from job_filter.api.schemas import (
    SyncTrackerRequest,
    UpdateApplicationStageRequest,
    UpdateStatusRequest,
)
from job_filter.llm.agy_client import LLMError
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


@router.get("/rescore-diff")
def preview_rescore_diff(conn: sqlite3.Connection = Depends(get_db)):
    """Сухой прогон пересчёта скоринга без записи в БД."""
    return skills_service.preview_rescore_diff(conn)


@router.get("/{job_id}/description")
def get_job_description_endpoint(
    job_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    desc = jobs_service.get_description(conn, job_id)
    if desc is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "description": desc}


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


@router.patch("/{job_id}/application-stage")
def update_job_application_stage(
    job_id: str,
    body: UpdateApplicationStageRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    ok = jobs_service.update_application_stage(
        conn,
        job_id=job_id,
        application_stage=body.application_stage,
        company_reject_reason=body.company_reject_reason,
        application_email_url=body.application_email_url,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job_id,
        "user_status": "applied",
        "application_stage": body.application_stage,
        "company_reject_reason": body.company_reject_reason,
        "application_email_url": body.application_email_url,
    }


@router.get("/applied-tracker/prompt")
def get_applied_tracker_prompt(
    skill_name: str = Query("@job-application-tracker"),
    conn: sqlite3.Connection = Depends(get_db),
):
    return jobs_service.get_tracker_prompt(conn, skill_name=skill_name)


@router.post("/applied-tracker/sync")
def sync_applied_tracker_endpoint(
    body: SyncTrackerRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        return jobs_service.sync_applied_tracker(
            conn,
            report_text=body.report_text,
            skill_name=body.skill_name,
            apply_updates=body.apply_updates,
        )
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))


