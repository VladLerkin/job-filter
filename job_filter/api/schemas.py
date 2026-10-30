"""Pydantic-схемы входящих HTTP-запросов API."""
from typing import Literal
from pydantic import BaseModel, Field

from job_filter import config


class RunPipelineRequest(BaseModel):
    search_terms: list[str] = [
        "Agentic Engineer Remote",
        "AI Agent Engineer Remote",
        "Software Engineer Remote",
    ]
    site_names: list[str] = ["linkedin"]
    location: str = "EMEA"
    country_indeed: str = "uk"
    results_wanted: int = 20
    hours_old: int = 4
    easy_apply: bool = False
    llm_model: str = config.DEFAULT_MODEL
    llm_limit: int = 15
    enrich_only: bool = False


class UpdateStatusRequest(BaseModel):
    user_status: Literal["new", "applied", "saved", "hidden"]


class CandidateProfileRequest(BaseModel):
    profile_text: str = ""
    cv_text: str = ""


class SkillCategoryRequest(BaseModel):
    category_id: str
    title: str
    multiplier: float = 2.0
    max_points: int = 30
    sort_order: int = 0


class CandidateSkillRequest(BaseModel):
    skill_id: str
    category_id: str
    name: str
    years_experience: float = 0.0
    weight_points: int | None = None
    is_primary: bool = False
    aliases: list[str] = []


class ApplyCVAnalysisRequest(BaseModel):
    update_cv_text: bool = True
    structured_cv: str = ""
    update_profile_text: bool = False
    candidate_summary: str = ""
    apply_skills: bool = True
    skills_to_apply: list[dict] = Field(default_factory=list)
    rescore_jobs: bool = False


class AddBlacklistRequest(BaseModel):
    domain_or_url: str | None = None
    company: str | None = None
    job_id: str | None = None
    reason: str = "Невозможно заполнить форму (в чёрном списке)"
    hide_job: bool = True
    use_last_opened: bool = False

