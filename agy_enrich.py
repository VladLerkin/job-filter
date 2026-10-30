"""Обратная совместимость: обогащение вакансий через LLM.

Реализация перенесена в `job_filter.llm`.
"""
from job_filter.config import AGY_BIN, DB_PATH, DEFAULT_MODEL, PROJECT_ROOT
from job_filter.llm.agy_client import extract_json_object, run_agy
from job_filter.llm.job_enricher import (
    SYSTEM_INSTRUCTIONS,
    build_enrich_prompt,
    enrich_job as enrich_job_with_agy,
    load_resume_text,
)

__all__ = [
    "AGY_BIN",
    "DB_PATH",
    "DEFAULT_MODEL",
    "PROJECT_ROOT",
    "SYSTEM_INSTRUCTIONS",
    "build_enrich_prompt",
    "enrich_job_with_agy",
    "extract_json_object",
    "load_resume_text",
    "run_agy",
]
