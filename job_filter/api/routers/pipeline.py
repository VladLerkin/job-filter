"""Роуты запуска и мониторинга фонового пайплайна поиска и скоринга."""
from fastapi import APIRouter
from job_filter.api.schemas import MacroSettingsRequest, RunMacroRequest, RunPipelineRequest
from job_filter.db.connection import connect
from job_filter.services.pipeline import (
    get_macro_settings,
    get_provider_check_status,
    save_macro_settings,
)
from job_filter.services.pipeline_runner import pipeline_runner

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/start")
def start_pipeline(req: RunPipelineRequest):
    started = pipeline_runner.start(req.model_dump())
    if not started:
        status = pipeline_runner.get_status()
        return {"status": "already_running", "logs_count": len(status["logs"])}
    return {"status": "started"}


@router.post("/start-macro")
def start_macro_pipeline(req: RunMacroRequest):
    payload = req.model_dump()
    payload["macro_mode"] = True
    started = pipeline_runner.start(payload)
    if not started:
        status = pipeline_runner.get_status()
        return {"status": "already_running", "logs_count": len(status["logs"])}
    return {"status": "started", "mode": "macro"}


@router.get("/status")
def get_pipeline_status(since: int = 0):
    status = pipeline_runner.get_status(since=since)
    conn = connect()
    try:
        status["provider_checks"] = get_provider_check_status(conn)
    finally:
        conn.close()
    return status


@router.get("/providers-status")
def get_providers_status():
    conn = connect()
    try:
        return {
            "provider_checks": get_provider_check_status(conn),
            "macro_settings": get_macro_settings(conn),
        }
    finally:
        conn.close()


@router.get("/macro-settings")
def read_macro_settings():
    conn = connect()
    try:
        return {
            "macro_settings": get_macro_settings(conn),
            "provider_checks": get_provider_check_status(conn),
        }
    finally:
        conn.close()


@router.put("/macro-settings")
def update_macro_settings(req: MacroSettingsRequest):
    conn = connect()
    try:
        saved = save_macro_settings(conn, req.model_dump())
        return {
            "status": "saved",
            "macro_settings": saved,
            "provider_checks": get_provider_check_status(conn),
        }
    finally:
        conn.close()


@router.post("/stop")
def stop_pipeline():
    stopped = pipeline_runner.stop()
    return {"status": "stopping" if stopped else "not_running"}


