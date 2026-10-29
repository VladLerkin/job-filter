import json
import re
import shutil
import subprocess
from pathlib import Path

from enrichment_schema import JobEnrichment

PROJECT_ROOT = Path(__file__).resolve().parent
RESUME_PATH = PROJECT_ROOT / "resume" / "resume.md"
PREFERENCES_PATH = PROJECT_ROOT / "resume" / "preferences.md"
EXTERNAL_RESUME_PATH = Path("/Users/vlad/IdeaProjects/hirify-filter-bot-export-skill/resume/resume.md")
EXTERNAL_PREFERENCES_PATH = Path("/Users/vlad/IdeaProjects/hirify-filter-bot-export-skill/resume/preferences.md")

AGY_BIN = shutil.which("agy") or "/Users/vlad/.local/bin/agy"
DEFAULT_MODEL = "gemini-3.8-flash-low"

SYSTEM_INSTRUCTIONS = """You extract structured job posting content for a candidate digest.
Ignore company marketing fluff in "About us" / "About the team" (do not copy long company paragraphs).

Return ONLY valid JSON matching this schema (no markdown fences, no commentary):
{
  "responsibilities": [string],
  "requirements": [string],
  "nice_to_have": [string],
  "required_technologies": [string],
  "nice_to_have_technologies": [string],
  "required_languages": [string],
  "nice_to_have_languages": [string],
  "resume_fit": {
    "score": integer 0-100,
    "summary": string or null,
    "matched_required": [string],
    "missing_required": [string],
    "matched_nice_to_have": [string]
  },
  "work_authorization": {
    "summary": string or null,
    "sponsorship": "yes" | "no" | "unclear",
    "eligible_regions": [string]
  },
  "location_restrictions": [string],
  "relocation_assistance": "yes" | "no" | "unclear",
  "relocation_benefits_detail": string or null,
  "remote_policy_detail": string or null,
  "degree_required": {
    "required": "yes" | "no" | "unclear",
    "detail": string or null
  }
}

Rules for role sections (from the job description only):
- responsibilities: what the person will do day-to-day. Up to 8 concise bullet strings.
- requirements: must-have qualifications (non-tech prose). Up to 8 bullets.
- nice_to_have: preferred qualifications (non-tech prose). Up to 6 bullets. [] if none.
- Each bullet: one line, short (max ~120 chars), no numbering prefix.

Rules for technology and language lists (from the job description only):
- required_technologies / nice_to_have_technologies: programming languages, frameworks, databases, clouds, tools, AI frameworks (e.g. Python, Java, Kotlin, Spring Boot, LangGraph, RAG, PostgreSQL, AWS, Kubernetes). Canonical short names. No duplicates across required vs nice.
- required_languages / nice_to_have_languages: human/spoken languages only (e.g. English B2+, German C1). Not programming languages.
- Up to 12 items per list. [] if not stated. Do not invent technologies not mentioned or clearly implied by the posting.

Rules for resume_fit (compare job to the candidate resume provided below):
- score 0-100: overlap on required tech/skills/experience; penalize missing hard required stack and language requirements.
- summary: one short sentence (max ~140 chars) in Russian explaining fit and any key gap or location note.
- matched_required: required tech + critical skills/languages the candidate clearly has per resume.
- missing_required: required tech/skills/languages the job needs but resume does not support.
- matched_nice_to_have: nice-to-have items the candidate has.
- Be honest; do not assume skills not in the resume.

Rules for constraints (CRITICAL for remote candidate in Georgia/Tbilisi):
- sponsorship "no" only if explicitly stated.
- location_restrictions: exact countries, regions, or timezones where candidate MUST reside or have work permit (e.g. ["UK only"], ["Poland"], ["EU/EEA only"], ["CET +/- 2h"], ["EMEA"], ["Worldwide"]).
- relocation_assistance / relocation_benefits_detail / remote_policy_detail / degree_required: use null, [], or "unclear" when not stated. Do not invent.
"""


def load_resume_text() -> str:
    resume_text = ""
    for path in (RESUME_PATH, EXTERNAL_RESUME_PATH):
        if path.is_file():
            resume_text = path.read_text(encoding="utf-8").strip()
            break

    prefs_text = ""
    for path in (PREFERENCES_PATH, EXTERNAL_PREFERENCES_PATH):
        if path.is_file():
            prefs_text = path.read_text(encoding="utf-8").strip()
            break

    combined = resume_text
    if prefs_text:
        combined += f"\n\n== CANDIDATE PREFERENCES & WORK AUTHORIZATION ==\n{prefs_text}"
    return combined[:12000]


def build_enrich_prompt(
    title: str,
    company: str | None,
    location: str | None,
    description: str,
) -> str:
    resume = load_resume_text()
    resume_block = (
        f"\n\n--- candidate resume (for resume_fit only) ---\n{resume}\n--- end resume ---"
        if resume
        else "\n\n(no resume file; set resume_fit score to 0)"
    )
    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"Job Title: {title}\n"
        f"Company: {company or 'not specified'}\n"
        f"Location (LinkedIn): {location or 'EMEA / Remote'}\n\n"
        f"Job Description:\n{description[:8000]}"
        f"{resume_block}"
    )


def extract_json_object(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    # Находим первую '{' и последнюю '}'
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def enrich_job_with_agy(
    title: str,
    company: str | None,
    location: str | None,
    description: str,
    model: str = DEFAULT_MODEL,
    timeout_sec: int = 90,
) -> JobEnrichment:
    prompt = build_enrich_prompt(title, company, location, description)
    cmd = [
        AGY_BIN,
        "--model",
        model,
        "--disable-slash-commands",
        "-p",
        prompt,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
    )
    if proc.returncode != 0:
        err_msg = (proc.stderr or proc.stdout or "").strip()[:400]
        raise RuntimeError(f"agy exited with {proc.returncode}: {err_msg}")

    raw = (proc.stdout or "").strip()
    if not raw:
        raise RuntimeError("agy returned empty response")

    data = extract_json_object(raw)
    return JobEnrichment.model_validate(data)

