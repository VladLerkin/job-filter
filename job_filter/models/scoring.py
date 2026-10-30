from pydantic import BaseModel, Field


class SkillScoreResult(BaseModel):
    score: int
    tier: str
    geo_passed: bool
    geo_reject_reason: str | None = None
    has_clean_title: bool = True
    title_penalty_tokens: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    breakdown: list[str] = Field(default_factory=list)
    match_category: str  # "top" (>=70), "good" (50..69), "low" (<50), "rejected_geo"

