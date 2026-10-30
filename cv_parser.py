"""Обратная совместимость: парсинг и ИИ-анализ PDF-резюме.

Реализация перенесена в `job_filter.llm.cv_analyzer` и `job_filter.services.cv_service`.
"""
from job_filter.llm.cv_analyzer import (
    CV_ANALYZER_SYSTEM_PROMPT,
    analyze_cv_text as analyze_cv_text_with_llm,
)
from job_filter.models.cv import ParsedCVResult, ParsedSkillItem
from job_filter.services.cv_service import (
    compute_skills_diff,
    extract_text_from_pdf_bytes,
)

__all__ = [
    "CV_ANALYZER_SYSTEM_PROMPT",
    "ParsedCVResult",
    "ParsedSkillItem",
    "analyze_cv_text_with_llm",
    "compute_skills_diff",
    "extract_text_from_pdf_bytes",
]
