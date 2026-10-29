from typing import Literal

from pydantic import BaseModel, Field

PROMPT_VERSION = "role-tech-resume-v3"

Sponsorship = Literal["yes", "no", "unclear"]
TriState = Literal["yes", "no", "unclear"]


class WorkAuthorization(BaseModel):
    summary: str | None = None
    sponsorship: Sponsorship = "unclear"
    eligible_regions: list[str] = Field(default_factory=list)


class DegreeRequired(BaseModel):
    required: TriState = "unclear"
    detail: str | None = None


class ResumeFit(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    summary: str | None = None
    matched_required: list[str] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)
    matched_nice_to_have: list[str] = Field(default_factory=list)


class JobEnrichment(BaseModel):
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
    required_technologies: list[str] = Field(default_factory=list)
    nice_to_have_technologies: list[str] = Field(default_factory=list)
    required_languages: list[str] = Field(default_factory=list)
    nice_to_have_languages: list[str] = Field(default_factory=list)
    resume_fit: ResumeFit = Field(default_factory=ResumeFit)
    work_authorization: WorkAuthorization = Field(default_factory=WorkAuthorization)
    location_restrictions: list[str] = Field(default_factory=list)
    relocation_assistance: TriState = "unclear"
    relocation_benefits_detail: str | None = None
    remote_policy_detail: str | None = None
    degree_required: DegreeRequired = Field(default_factory=DegreeRequired)


JobConstraintsEnrichment = JobEnrichment

