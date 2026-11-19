"""Роуты взаимодействия с FreeHire Public/Agent API (живые фасеты, счётчики и подбор навыков из профиля)."""
import logging
import math
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from job_filter.api.deps import get_db
from job_filter.repositories import blacklist_repo
from job_filter.scoring.matrix import extract_candidate_aliases, get_skill_matrix
from job_filter.scraping.freehire_adapter import (
    DEFAULT_FREEHIRE_FACETS,
    FreeHireClient,
    map_blacklisted_domains_to_freehire_sources,
    match_profile_skills_to_freehire,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/freehire", tags=["freehire"])

# Основные фасеты, которые мы возвращаем в UI для компактного и быстрого ответа
UI_FACET_KEYS = [
    "ai_archetype",
    "category",
    "seniority",
    "work_mode",
    "regions",
    "skills",
    "reality",
    "posting_language",
    "source_type",
]


class FreeHireFacetsRequest(BaseModel):
    facets: dict[str, Any] = Field(default_factory=dict)
    hours_old: int | None = None


@router.get("/defaults")
def get_freehire_defaults():
    """Возвращает дефолтную конфигурацию фасетов FreeHire."""
    return {"defaults": DEFAULT_FREEHIRE_FACETS}


@router.post("/facets")
def query_freehire_facets(req: FreeHireFacetsRequest, conn=Depends(get_db)):
    """Проксирует /api/v1/jobs/facets с учётом текущих фильтров и возвращает живые счётчики."""
    client = FreeHireClient()
    eff_facets = dict(req.facets or {})
    if req.hours_old and req.hours_old > 0 and not eff_facets.get("posted_within_days"):
        eff_facets["posted_within_days"] = max(1, math.ceil(req.hours_old / 24.0))

    extra_source_exclude: list[str] = []
    if eff_facets.get("exclude_blacklisted_ats", True):
        domains = blacklist_repo.list_board_domains(conn)
        extra_source_exclude = map_blacklisted_domains_to_freehire_sources(domains)

    try:
        data = client.get_facets(
            eff_facets,
            facet_keys=UI_FACET_KEYS,
            extra_source_exclude=extra_source_exclude,
        )
        raw_facets = data.get("facets") or {}

        # Ограничиваем список skills до топ-60 для компактности ответа UI
        trimmed_facets: dict[str, dict[str, int]] = {}
        for k, v in raw_facets.items():
            if not isinstance(v, dict):
                continue
            if k == "skills":
                top_skills = sorted(v.items(), key=lambda x: -int(x[1]))[:60]
                trimmed_facets[k] = {sk: int(cnt) for sk, cnt in top_skills}
            else:
                sorted_items = sorted(v.items(), key=lambda x: -int(x[1]))
                trimmed_facets[k] = {sk: int(cnt) for sk, cnt in sorted_items}

        return {
            "ok": True,
            "total": int(data.get("total") or 0),
            "facets": trimmed_facets,
            "excluded_ats_sources": extra_source_exclude,
        }
    except Exception as exc:
        logger.error("Ошибка при получении фасетов FreeHire: %s", exc)
        return {
            "ok": False,
            "error": str(exc),
            "total": 0,
            "facets": {},
            "excluded_ats_sources": extra_source_exclude,
        }


@router.get("/profile-skills")
def get_freehire_profile_skills(conn=Depends(get_db)):
    """Сопоставляет Skills Matrix кандидата с каноническими слагами фасета `skills` FreeHire."""
    matrix = get_skill_matrix(conn)
    aliases = extract_candidate_aliases(matrix)
    client = FreeHireClient()
    try:
        base_data = client.get_facets(facet_keys=["skills"], use_base_cache=False)
        available_skills = (base_data.get("facets") or {}).get("skills") or {}
        matched = match_profile_skills_to_freehire(aliases, available_skills, max_skills=15)
        return {
            "ok": True,
            "skills": matched,
        }
    except Exception as exc:
        logger.error("Ошибка сопоставления навыков профиля с FreeHire: %s", exc)
        return {
            "ok": False,
            "error": str(exc),
            "skills": [],
        }
