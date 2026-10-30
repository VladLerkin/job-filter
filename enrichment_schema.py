"""Обратная совместимость: Pydantic-модели обогащения вакансий.

Реализация перенесена в `job_filter.models.enrichment`.
"""
from job_filter.models.enrichment import (
    DegreeRequired,
    JobConstraintsEnrichment,
    JobEnrichment,
    ResumeFit,
    Sponsorship,
    TriState,
    WorkAuthorization,
)

PROMPT_VERSION = "role-tech-resume-v3"

__all__ = [
    "DegreeRequired",
    "JobConstraintsEnrichment",
    "JobEnrichment",
    "PROMPT_VERSION",
    "ResumeFit",
    "Sponsorship",
    "TriState",
    "WorkAuthorization",
]
