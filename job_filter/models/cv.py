"""Модели результата ИИ-разбора PDF-резюме."""
import re

from pydantic import BaseModel, Field, model_validator


class ParsedSkillItem(BaseModel):
    skill_id: str
    name: str = ""
    category_id: str = "core_backend"
    years_experience: float = 0.0
    is_primary: bool = False
    aliases: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data):
        if not isinstance(data, dict):
            return data
        # Handle 'category' alias for 'category_id'
        if "category_id" not in data and "category" in data:
            data["category_id"] = data["category"]
        if "name" not in data or not data["name"]:
            data["name"] = data.get("skill_id", "")
        # Handle years_experience if passed as string (e.g. "5+", "5 years")
        years = data.get("years_experience", 0.0)
        if isinstance(years, str):
            m = re.search(r"(\d+(?:\.\d+)?)", years)
            data["years_experience"] = float(m.group(1)) if m else 0.0
        elif years is None:
            data["years_experience"] = 0.0
        return data


class ParsedCVResult(BaseModel):
    candidate_summary: str = ""
    structured_cv_markdown: str = ""
    total_years_experience: float = 0.0
    skills: list[ParsedSkillItem] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data):
        if not isinstance(data, dict):
            return data
        # Sometimes LLMs name the skills array differently
        if "skills" not in data:
            for alt in ("extracted_skills", "technical_skills", "candidate_skills", "skill_list"):
                if alt in data and isinstance(data[alt], list):
                    data["skills"] = data[alt]
                    break
        return data

