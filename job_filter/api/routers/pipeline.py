"""Роуты запуска и мониторинга фонового пайплайна поиска и скоринга."""
from fastapi import APIRouter
from job_filter.api.schemas import RunPipelineRequest
from job_filter.services.pipeline_runner import pipeline_runner

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/start")
def start_pipeline(req: RunPipelineRequest):
    started = pipeline_runner.start(req.model_dump())
    if not started:
        status = pipeline_runner.get_status()
        return {"status": "already_running", "logs_count": len(status["logs"])}
    return {"status": "started"}


@router.get("/status")
def get_pipeline_status(since: int = 0):
    return pipeline_runner.get_status(since=since)

