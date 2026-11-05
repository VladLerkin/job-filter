"""Роуты профиля кандидата, загрузки PDF-резюме и применения распознанных навыков."""
import logging
import sqlite3
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from job_filter import config
from job_filter.api.deps import get_db
from job_filter.api.schemas import ApplyCVAnalysisRequest, CandidateProfileRequest
from job_filter.llm.cv_analyzer import analyze_cv_text
from job_filter.repositories import candidate_repo, skills_repo
from job_filter.services import cv_service, skills_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/candidate", tags=["candidate"])


@router.get("")
def read_candidate_profile(conn: sqlite3.Connection = Depends(get_db)):
    return candidate_repo.get_settings(conn)


@router.put("")
def update_candidate_profile(
    body: CandidateProfileRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    return candidate_repo.save_settings(
        conn,
        body.profile_text,
        body.cv_text,
        body.geo_preferences,
    )


@router.post("/upload-cv-pdf")
async def upload_and_analyze_cv_pdf(
    file: UploadFile = File(...),
    model: str = config.DEFAULT_MODEL,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Принимает файл PDF с резюме, извлекает текст и анализирует через LLM."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Поддерживаются только файлы в формате PDF (.pdf)")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Загружен пустой файл")

    logger.info("PDF upload received: %s (%d bytes). Extracting text...", file.filename, len(pdf_bytes))

    try:
        raw_text = cv_service.extract_text_from_pdf_bytes(pdf_bytes)
    except Exception as e:
        logger.error("Failed to extract text from PDF %s: %s", file.filename, e)
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("Extracted %d characters from PDF. Starting LLM analysis...", len(raw_text))

    matrix = skills_repo.get_matrix(conn)
    categories = matrix.get("categories", [])
    existing_skills = matrix.get("skills", [])
    effective_categories = cv_service.get_effective_categories(categories)

    try:
        parsed = analyze_cv_text(raw_text, effective_categories, model=model)
    except Exception as e:
        logger.error("LLM CV analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Ошибка ИИ-анализа резюме: {e}")

    diff = cv_service.compute_skills_diff(parsed.skills, existing_skills, effective_categories)
    new_c = sum(1 for s in diff if s["status"] == "new")
    upd_c = sum(1 for s in diff if s["status"] == "updated")
    unch_c = sum(1 for s in diff if s["status"] == "unchanged")
    logger.info("CV analysis complete: %d skills in diff (new: %d, updated: %d, unchanged: %d)", len(diff), new_c, upd_c, unch_c)

    return {
        "raw_text_length": len(raw_text),
        "filename": file.filename,
        "structured_cv": parsed.structured_cv_markdown,
        "candidate_summary": parsed.candidate_summary,
        "total_years_experience": parsed.total_years_experience,
        "skills_diff": diff,
        "available_categories": effective_categories,
    }


@router.post("/apply-cv-analysis")
def apply_cv_analysis(
    body: ApplyCVAnalysisRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    skills_applied, cv_updated = cv_service.apply_cv_analysis(
        conn,
        update_cv_text=body.update_cv_text,
        structured_cv=body.structured_cv,
        update_profile_text=body.update_profile_text,
        candidate_summary=body.candidate_summary,
        apply_skills=body.apply_skills,
        skills_to_apply=body.skills_to_apply,
    )
    rescored = 0
    if body.rescore_jobs:
        rescored = skills_service.rescore_all_jobs(conn)

    return {
        "status": "ok",
        "cv_updated": cv_updated,
        "skills_applied": skills_applied,
        "rescored": rescored,
    }

