import io
import json
import logging
import re
import subprocess
import time
from pathlib import Path
from pydantic import BaseModel, Field, model_validator
from pypdf import PdfReader

from agy_enrich import AGY_BIN, DEFAULT_MODEL, extract_json_object

logger = logging.getLogger(__name__)


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


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Извлекает и нормализует текстовый слой из переданного PDF файла."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ValueError(f"Не удалось открыть PDF файл: {e}")

    pages_text = []
    for idx, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(text.strip())
        except Exception:
            continue

    combined = "\n\n".join(pages_text)
    # Нормализация переносов строк и повторяющихся пробелов
    combined = re.sub(r"(\w+)-\n(\w+)", r"\1\2", combined)
    combined = re.sub(r"[ \t]+", " ", combined)

    if len(combined.strip()) < 50:
        raise ValueError(
            "В PDF-файле не обнаружен текстовый слой (возможно, это отсканированный документ или изображение). "
            "Пожалуйста, загрузите PDF с текстовым слоем или скопируйте текст вручную."
        )
    return combined.strip()


CV_ANALYZER_SYSTEM_PROMPT = """You are an expert HR Tech & AI Resume Analyst.
Your task is to take raw resume text extracted from a candidate's PDF and perform two jobs:

1. Re-format, clean, and structure it into a clean, professional, readable Markdown CV:
   - Fix broken hyphenation, weird PDF line wraps, and scrambled spacing.
   - Include: Professional Title & Summary, Key Technologies, Work Experience (Company, Role, Dates, Achievements & Tech Stack used), Education & Certifications.
   - Retain all meaningful facts, project details, numbers, and dates from the original CV.
   - Output language: English (matching standard global CV format).

2. Extract Candidate Summary (candidate_summary):
   - A concise summary (1-3 sentences in Russian) highlighting total years of experience, primary specialty (e.g. Senior Backend / Agentic AI Engineer), and core languages/frameworks.

3. Extract Skills & Years of Experience (skills):
   - Extract ALL distinct technical skills, frameworks, message brokers, databases, and architectural concepts used in the candidate's career.
   - skill_id: lowercase slug (e.g. "langgraph", "java", "kotlin", "spring_boot", "kafka", "docker", "fintech").
   - name: clear standard display title (e.g. "LangGraph", "Java", "Spring Boot", "Kafka").
   - category_id: assign each skill to the most appropriate category ID from the Available Categories list provided below.
   - years_experience: calculate realistic total years of experience based on the start/end dates of jobs where this skill was used. (e.g. 10.0, 5.0, 2.5). Be accurate and realistic.
   - is_primary: true if this is one of candidate's core languages / primary specializations, false if secondary or auxiliary.
   - aliases: 2 to 5 common lowercase synonyms/tokens for matching (e.g. ["spring", "spring boot", "spring data"]).

Return ONLY valid JSON matching the requested schema.
"""


def analyze_cv_text_with_llm(
    cv_raw_text: str,
    categories: list[dict],
    model: str = DEFAULT_MODEL,
    timeout_sec: int = 120,
) -> ParsedCVResult:
    if not categories:
        from skill_scorer import _build_fallback_matrix
        categories = _build_fallback_matrix()["categories"]

    cat_descriptions = "\n".join(
        f"- ID: '{c['category_id']}', Title: '{c['title']}', Multiplier: {c['multiplier']}x, Max: {c['max_points']} pts"
        for c in categories
    )

    schema_format = """{
  "candidate_summary": "1-3 sentences in Russian summarizing candidate experience, main stack and role",
  "structured_cv_markdown": "# Candidate Name\\n\\n## Summary\\n...\\n\\n## Experience\\n...",
  "total_years_experience": 10.0,
  "skills": [
    {
      "skill_id": "langgraph",
      "name": "LangGraph",
      "category_id": "ai_agentic",
      "years_experience": 2.0,
      "is_primary": true,
      "aliases": ["langgraph", "langchain"]
    }
  ]
}"""

    prompt = (
        f"{CV_ANALYZER_SYSTEM_PROMPT}\n\n"
        f"Available Skill Categories in the System:\n{cat_descriptions}\n\n"
        f"Output JSON Format Specification (respond ONLY with this JSON structure):\n"
        f"{schema_format}\n\n"
        f"--- RAW RESUME TEXT (from PDF) ---\n"
        f"{cv_raw_text[:14000]}\n"
        f"--- END RAW RESUME TEXT ---"
    )

    cmd = [
        AGY_BIN,
        "--model",
        model,
        "--disable-slash-commands",
        "-p",
        prompt,
    ]

    t0 = time.time()
    logger.info("Calling LLM (%s) to analyze CV text (%d chars)...", model, len(cv_raw_text))
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    duration = time.time() - t0
    if proc.returncode != 0:
        logger.error("LLM CV analysis failed in %.1fs: %s", duration, proc.stderr.strip())
        raise RuntimeError(f"LLM processing error (code {proc.returncode}): {proc.stderr.strip()}")

    logger.info("LLM CV analysis completed in %.1fs. Raw output length: %d chars", duration, len(proc.stdout))
    try:
        data = extract_json_object(proc.stdout)
    except Exception as e:
        logger.error("Failed to extract JSON from LLM output: %s\nFirst 500 chars:\n%s", e, proc.stdout[:500])
        raise

    res = ParsedCVResult.model_validate(data)
    logger.info("Parsed CV successfully: %d skills, %.1f total years experience", len(res.skills), res.total_years_experience)
    return res


def compute_skills_diff(
    extracted_skills: list[ParsedSkillItem],
    existing_skills: list[dict],
    categories: list[dict],
) -> list[dict]:
    """
    Сравнивает извлеченные ИИ навыки с существующими в базе данными candidate_skills.
    Возвращает структурированный diff для модального окна подтверждения в UI.
    """
    cat_map = {c["category_id"]: c for c in categories}
    default_cat_id = categories[0]["category_id"] if categories else "core_backend"

    exist_map = {s["skill_id"]: s for s in existing_skills}
    seen_skill_ids = set()

    diff_list = []

    for es in extracted_skills:
        sid = es.skill_id.strip().lower()
        if not sid:
            continue
        seen_skill_ids.add(sid)

        cid = es.category_id.strip().lower()
        if cid not in cat_map:
            cid = default_cat_id
        cat = cat_map.get(cid, {})
        mult = float(cat.get("multiplier", 2.0))
        max_p = int(cat.get("max_points", 20))

        # Вычисляем предварительные баллы скоринга
        if mult < 0:
            new_points = max_p
        else:
            new_points = min(round(es.years_experience * mult), max_p)

        if sid in exist_map:
            existing = exist_map[sid]
            old_years = float(existing.get("years_experience", 0.0))
            old_points = int(existing.get("weight_points", 0))
            is_changed = (abs(old_years - es.years_experience) >= 0.25) or (old_points != new_points)

            diff_list.append({
                "skill_id": sid,
                "name": es.name,
                "category_id": cid,
                "category_title": cat.get("title", cid),
                "status": "updated" if is_changed else "unchanged",
                "selected": is_changed,  # по умолчанию выбраны только изменившиеся
                "old_years": old_years,
                "new_years": es.years_experience,
                "old_points": old_points,
                "new_points": new_points,
                "is_primary": es.is_primary,
                "aliases": es.aliases or [sid],
            })
        else:
            diff_list.append({
                "skill_id": sid,
                "name": es.name,
                "category_id": cid,
                "category_title": cat.get("title", cid),
                "status": "new",
                "selected": True,  # новые навыки выбраны по умолчанию
                "old_years": 0.0,
                "new_years": es.years_experience,
                "old_points": 0,
                "new_points": new_points,
                "is_primary": es.is_primary,
                "aliases": es.aliases or [sid],
            })

    # Сортировка: сначала новые, затем обновленные, затем без изменений
    status_order = {"new": 0, "updated": 1, "unchanged": 2}
    diff_list.sort(key=lambda x: (status_order.get(x["status"], 9), -x["new_points"], x["name"]))

    return diff_list

