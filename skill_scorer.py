"""Обратная совместимость: модуль скоринга вакансий.

Реализация перенесена в `job_filter.scoring` и `job_filter.db.seed_data`.
"""
from job_filter.db.seed_data import DEFAULT_CANDIDATE_SKILLS, default_skill_matrix as _build_fallback_matrix
from job_filter.models.scoring import SkillScoreResult
from job_filter.scoring.geo import classify_geo_tier
from job_filter.scoring.matrix import (
    extract_candidate_aliases,
    get_skill_matrix as get_loaded_skill_matrix,
    invalidate_matrix_cache as invalidate_skill_matrix_cache,
    skill_matches_candidate as _skill_matches_candidate,
)
from job_filter.scoring.scorer import (
    NON_PROFILE_TITLE_KEYWORDS,
    score_vacancy_by_skill,
)

DEFAULT_CANDIDATE_SKILLS_SET = {
    alias.strip().lower()
    for s in _build_fallback_matrix()["skills"]
    for alias in ([s["name"]] + s.get("aliases", []))
    if alias and alias.strip()
}

__all__ = [
    "SkillScoreResult",
    "classify_geo_tier",
    "score_vacancy_by_skill",
    "get_loaded_skill_matrix",
    "invalidate_skill_matrix_cache",
    "_build_fallback_matrix",
    "_skill_matches_candidate",
    "DEFAULT_CANDIDATE_SKILLS_SET",
    "NON_PROFILE_TITLE_KEYWORDS",
]
