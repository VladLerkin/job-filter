import io
import json
import re
import subprocess
from pathlib import Path
from pydantic import BaseModel, Field
from pypdf import PdfReader

from agy_enrich import AGY_BIN, DEFAULT_MODEL, extract_json_object


class ParsedSkillItem(BaseModel):
    skill_id: str
    name: str
    category_id: str
    years_experience: float = 0.0
    is_primary: bool = False
    aliases: list[str] = Field(default_factory=list)


class ParsedCVResult(BaseModel):
    candidate_summary: str = ""
    structured_cv_markdown: str = ""
    total_years_experience: float = 0.0
    skills: list[ParsedSkillItem] = Field(default_factory=list)


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
    cat_descriptions = "\n".join(
        f"- ID: '{c['category_id']}', Title: '{c['title']}', Multiplier: {c['multiplier']}x, Max: {c['max_points']} pts"
        for c in categories
    )

    prompt = (
        f"{CV_ANALYZER_SYSTEM_PROMPT}\n\n"
        f"Available Skill Categories in the System:\n{cat_descriptions}\n\n"
        f"--- RAW RESUME TEXT (from PDF) ---\n"
        f"{cv_raw_text[:14000]}\n"
        f"--- END RAW RESUME TEXT ---"
    )

    schema_str = json.dumps(ParsedCVResult.model_json_schema())
    cmd = [
        AGY_BIN,
        "--model",
        model,
        "--disable-slash-commands",
        "--output-format",
        "json",
        "--json-schema",
        schema_str,
        "-p",
        prompt,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    if proc.returncode != 0:
        raise RuntimeError(f"LLM processing error (code {proc.returncode}): {proc.stderr.strip()}")

    data = extract_json_object(proc.stdout)
    return ParsedCVResult.model_validate(data)


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

