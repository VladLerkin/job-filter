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
    results_wanted: int = 50
    hours_old: int = 4
    easy_apply: bool = False
    llm_model: str = config.DEFAULT_MODEL
    llm_limit: int = 50
    enrich_only: bool = False
    hirify_mode: Literal["feeds", "custom"] = "feeds"
    hirify_feed_id: int | str | None = None


class UpdateStatusRequest(BaseModel):
    user_status: Literal["new", "applied", "saved", "hidden", "rejected"]
    user_reject_reason: str | None = None


class UpdateApplicationStageRequest(BaseModel):
    application_stage: Literal["applied", "confirmed", "interview", "rejected_by_company"]
    company_reject_reason: str | None = None
    application_email_url: str | None = None


class SyncTrackerRequest(BaseModel):
    report_text: str | None = None
    skill_name: str = "@job-application-tracker"
    apply_updates: bool = True


class CandidateProfileRequest(BaseModel):
    profile_text: str = ""
    cv_text: str = ""
    geo_preferences: dict | None = None


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


class MacroStepConfig(BaseModel):
    site: Literal["hirify", "linkedin", "indeed", "glassdoor", "upwork"]
    enabled: bool = True
    locations: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    hirify_mode: Literal["feeds", "custom"] = "feeds"
    hirify_feed_id: int | str | None = None
    easy_apply: bool = False


class MacroSettingsRequest(BaseModel):
    execution_mode: Literal["per_provider", "batch_all_then_llm"] = "per_provider"
    hours_mode: Literal["auto_from_last_run", "fixed"] = "auto_from_last_run"
    default_hours_old: int = 8
    max_auto_hours_old: int = 72
    results_wanted: int = 50
    llm_limit: int = 50
    steps: list[MacroStepConfig] = Field(default_factory=list)


class RunMacroRequest(BaseModel):
    search_terms: list[str] = [
        "Agentic Engineer Remote",
        "AI Agent Engineer Remote",
        "Software Engineer Remote",
    ]
    llm_model: str = config.DEFAULT_MODEL
    macro_settings: dict | None = None


