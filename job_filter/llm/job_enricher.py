"""LLM-разбор вакансии в структурированный JobEnrichment (требования, стек, гео-ограничения, fit с резюме)."""
from job_filter import config
from job_filter.db.connection import db_session
from job_filter.llm.agy_client import extract_json_object, run_agy, unwrap_structured_output
from job_filter.models.enrichment import JobEnrichment
from job_filter.repositories import candidate_repo

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
  },
  "candidate_geo_eligibility": "yes" | "no" | "unclear",
  "work_arrangement": "remote_only" | "hybrid_required" | "onsite_required" | "remote_or_hybrid_optional" | "unknown"
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

Rules for constraints & geographic eligibility:
- Evaluate remote work eligibility, constraints, and resume_fit strictly against the CANDIDATE LOCATION & REMOTE WORK PREFERENCES provided below.
- sponsorship "no" only if explicitly stated as no visa sponsorship / no relocation.
- location_restrictions: exact countries, regions, or timezones where candidate MUST reside or have work permit (e.g. ["UK only"], ["Poland"], ["EU/EEA only"], ["CET +/- 2h"], ["EMEA"], ["Worldwide"]).
- relocation_assistance: "yes" if company explicitly provides visa sponsorship or relocation package; "no" if explicitly stated as no sponsorship/relocation; "unclear" if not stated.
- relocation_benefits_detail / remote_policy_detail / degree_required: use null, [], or "unclear" when not stated. Do not invent.
- candidate_geo_eligibility: evaluate whether the candidate is eligible for this role based on CANDIDATE LOCATION & REMOTE WORK PREFERENCES.
  * "yes": Candidate's base location matches (e.g. Georgia / Caucasus / open Eastern Europe / broad EMEA / Worldwide remote), OR company explicitly provides Visa Sponsorship / Relocation assistance.
  * "no": Role strictly requires residency, local citizenship, or tax residency in a specific foreign country or restricted country pool (e.g. Czechia/Slovakia/Hungary only, US only, UK only, Germany only, EU/EEA only) with NO relocation assistance.
  * "unclear": Location constraints are not clearly specified or role is open remote.
- work_arrangement:
  * "remote_only": 100% remote work without mandatory office attendance.
  * "remote_or_hybrid_optional": Candidate can work 100% remotely, while office or hybrid attendance is optional.
  * "hybrid_required": Mandatory hybrid schedule requiring regular attendance at a physical office (e.g. 2-3 days/week or 50% telework).
  * "onsite_required": Full-time on-site office role.
  * "unknown": Not specified.
"""

RESUME_MAX_CHARS = 12000


def format_geo_preferences_prompt(geo_prefs: dict | None, profile_text: str = "") -> str:
    """Формирует структурированный блок географических предпочтений кандидата для передачи в LLM."""
    prefs = geo_prefs or {}
    loc = prefs.get("current_location", "Georgia, Tbilisi (UTC+4)")
    macro_list = prefs.get("allowed_macro_regions") or ["Georgia", "Caucasus", "Eastern Europe", "CEE", "EMEA"]
    macro = ", ".join(macro_list) if isinstance(macro_list, list) else str(macro_list)
    ww = "Allowed (Candidate is available for Global Remote via B2B/Contractor)" if prefs.get("allow_worldwide_remote", True) else "Disallowed"
    relo_pol = prefs.get("relocation_policy", "with_sponsorship_only")
    relo_desc = {
        "with_sponsorship_only": "Candidate considers foreign roles ONLY if company provides Visa Sponsorship or Relocation assistance.",
        "no_relocation": "Remote only, candidate will not relocate.",
        "open_to_relocation": "Candidate is actively open to relocation for suitable roles.",
    }.get(relo_pol, relo_pol)
    notes = prefs.get("custom_notes", "")

    lines = [
        "=== CANDIDATE LOCATION & REMOTE WORK PREFERENCES ===",
        f"- Current Base Location: {loc}",
        f"- Target Local & Macro-Regions: {macro}",
        f"- Global Remote (Worldwide / Anywhere): {ww}",
        f"- Relocation Policy: {relo_desc}",
    ]
    if prefs.get("reject_unsupported_single_country", True):
        lines.append(
            f"- Constraint Rule: If the role strictly requires physical residency/work authorization within a single foreign country (e.g. US only, UK only, Germany only, EU/EEA only) with NO relocation assistance, explicitly record it in location_restrictions as restricted and ineligible for remote from candidate's base location ({loc})."
        )
    if prefs.get("reject_business_travel", True):
        lines.append(
            "- Business Travel Policy: Candidate does NOT accept roles requiring regular business travel, visits to factories/client sites, or mandatory periodic office visits. Record any required travel or on-site visits in remote_policy_detail and requirements."
        )
    if notes:
        lines.append(f"- Additional Candidate Notes: {notes}")
    if profile_text:
        lines.append(f"- Candidate Profile & Work Authorization Comments:\n{profile_text}")

    return "\n".join(lines)


def load_candidate_context() -> tuple[str, str]:
    """Загружает текст резюме и отформатированный блок гео-преференций из БД."""
    try:
        with db_session() as conn:
            settings = candidate_repo.get_settings(conn)
    except Exception:
        return "", ""
    resume_text = (settings.get("cv_text") or "").strip()
    profile_text = (settings.get("profile_text") or "").strip()
    geo_prefs = settings.get("geo_preferences") or {}

    geo_block = format_geo_preferences_prompt(geo_prefs, profile_text)
    return resume_text[:RESUME_MAX_CHARS], geo_block


def load_resume_text() -> str:
    """Резюме + предпочтения кандидата из БД (обратная совместимость)."""
    cv_text, geo_block = load_candidate_context()
    if geo_block:
        return f"{cv_text}\n\n{geo_block}"[:RESUME_MAX_CHARS]
    return cv_text[:RESUME_MAX_CHARS]


def build_enrich_prompt(
    title: str,
    company: str | None,
    location: str | None,
    description: str,
    resume: str,
    geo_context: str = "",
) -> str:
    resume_block = (
        f"\n\n--- candidate resume (for resume_fit only) ---\n{resume}\n--- end resume ---"
        if resume
        else "\n\n(no resume file; set resume_fit score to 0)"
    )
    geo_section = f"\n\n{geo_context}\n" if geo_context else ""
    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"Job Title: {title}\n"
        f"Company: {company or 'not specified'}\n"
        f"Location (LinkedIn): {location or 'EMEA / Remote'}\n\n"
        f"Job Description:\n{description[:8000]}"
        f"{geo_section}"
        f"{resume_block}"
    )


def enrich_job(
    title: str,
    company: str | None,
    location: str | None,
    description: str,
    model: str | None = None,
    resume: str | None = None,
    timeout_sec: int = config.JOB_ENRICH_TIMEOUT_SEC,
    geo_context: str | None = None,
) -> JobEnrichment:
    """Отправляет вакансию в LLM. `resume` и `geo_context` можно передать заранее, чтобы не читать БД на каждую вакансию."""
    if resume is None or geo_context is None:
        cand_resume, cand_geo = load_candidate_context()
        if resume is None:
            resume = cand_resume
        if geo_context is None:
            geo_context = cand_geo

    prompt = build_enrich_prompt(title, company, location, description, resume, geo_context=geo_context or "")
    raw = run_agy(prompt, model=model, timeout_sec=timeout_sec, json_schema=JobEnrichment.model_json_schema())
    data = unwrap_structured_output(extract_json_object(raw))
    return JobEnrichment.model_validate(data)
