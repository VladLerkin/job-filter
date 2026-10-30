"""LLM-анализ текста резюме: структурированный Markdown CV, краткое саммари и навыки с годами опыта."""
import logging

from job_filter import config
from job_filter.db.seed_data import DEFAULT_SKILL_CATEGORIES
from job_filter.llm.agy_client import extract_json_object, run_agy
from job_filter.models.cv import ParsedCVResult

logger = logging.getLogger(__name__)

CV_TEXT_MAX_CHARS = 14000

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

OUTPUT_FORMAT_EXAMPLE = """{
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


def build_cv_prompt(cv_raw_text: str, categories: list[dict]) -> str:
    cat_descriptions = "\n".join(
        f"- ID: '{c['category_id']}', Title: '{c['title']}', Multiplier: {c['multiplier']}x, Max: {c['max_points']} pts"
        for c in categories
    )
    return (
        f"{CV_ANALYZER_SYSTEM_PROMPT}\n\n"
        f"Available Skill Categories in the System:\n{cat_descriptions}\n\n"
        f"Output JSON Format Specification (respond ONLY with this JSON structure):\n"
        f"{OUTPUT_FORMAT_EXAMPLE}\n\n"
        f"--- RAW RESUME TEXT (from PDF) ---\n"
        f"{cv_raw_text[:CV_TEXT_MAX_CHARS]}\n"
        f"--- END RAW RESUME TEXT ---"
    )


def analyze_cv_text(
    cv_raw_text: str,
    categories: list[dict],
    model: str | None = None,
    timeout_sec: int = config.CV_ANALYZE_TIMEOUT_SEC,
) -> ParsedCVResult:
    # --json-schema не используется: на вложенных $defs agy CLI зависает, формат задаётся примером в промпте
    if not categories:
        categories = DEFAULT_SKILL_CATEGORIES
    logger.info("Analyzing CV text (%d chars) with LLM...", len(cv_raw_text))
    raw = run_agy(build_cv_prompt(cv_raw_text, categories), model=model, timeout_sec=timeout_sec)
    try:
        data = extract_json_object(raw)
    except Exception as e:
        logger.error("Failed to extract JSON from LLM output: %s\nFirst 500 chars:\n%s", e, raw[:500])
        raise
    result = ParsedCVResult.model_validate(data)
    logger.info("Parsed CV: %d skills, %.1f total years", len(result.skills), result.total_years_experience)
    return result
