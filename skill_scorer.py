import re
from datetime import date, datetime
from pydantic import BaseModel, Field

from enrichment_schema import JobEnrichment

import json
import re
import sqlite3
from datetime import date, datetime
from pydantic import BaseModel, Field

from enrichment_schema import JobEnrichment

# Кэш матрицы навыков из базы данных
_SKILL_MATRIX_CACHE: dict | None = None


def invalidate_skill_matrix_cache():
    global _SKILL_MATRIX_CACHE
    _SKILL_MATRIX_CACHE = None


def _build_fallback_matrix() -> dict:
    return {
        "categories": [
            {"category_id": "ai_agentic", "title": "🤖 AI & Agentic Systems", "multiplier": 15.0, "max_points": 30, "sort_order": 1},
            {"category_id": "core_backend", "title": "☕ Core Backend & Languages", "multiplier": 2.0, "max_points": 20, "sort_order": 2},
            {"category_id": "secondary_backend", "title": "🐍 Secondary Languages / TS", "multiplier": 3.0, "max_points": 18, "sort_order": 3},
            {"category_id": "arch_infra", "title": "🏗️ Architecture & Cloud / DevOps", "multiplier": 2.0, "max_points": 15, "sort_order": 4},
            {"category_id": "domains", "title": "💼 Business Domains (FinTech / Banking)", "multiplier": 2.0, "max_points": 10, "sort_order": 5},
            {"category_id": "alien", "title": "🚫 Чужой стек (Штрафы)", "multiplier": -1.0, "max_points": -20, "sort_order": 6},
            {"category_id": "legacy", "title": "🦖 Устаревший стек (Штрафы)", "multiplier": -1.0, "max_points": -30, "sort_order": 7},
        ],
        "skills": [
            {"skill_id": "langgraph", "category_id": "ai_agentic", "name": "LangGraph", "years_experience": 2.0, "weight_points": 30, "is_primary": 1, "aliases": ["langgraph", "langchain", "crewai", "koog"]},
            {"skill_id": "agentic", "category_id": "ai_agentic", "name": "AI Agents / Multi-Agent", "years_experience": 2.0, "weight_points": 30, "is_primary": 1, "aliases": ["agentic", "agentic ai", "ai agentic", "ai agents", "agents", "multi-agent", "multi agent", "a2a"]},
            {"skill_id": "rag", "category_id": "ai_agentic", "name": "RAG & Vector DB", "years_experience": 2.0, "weight_points": 20, "is_primary": 1, "aliases": ["rag", "embeddings", "vector db", "mem0", "memsearch"]},
            {"skill_id": "mcp", "category_id": "ai_agentic", "name": "MCP Protocol", "years_experience": 1.5, "weight_points": 20, "is_primary": 1, "aliases": ["mcp", "model context protocol"]},
            {"skill_id": "llm", "category_id": "ai_agentic", "name": "LLMs / GenAI / Prompt Engineering", "years_experience": 2.5, "weight_points": 25, "is_primary": 1, "aliases": ["llm", "llms", "genai", "generative ai", "prompt engineering", "claude", "openai", "anthropic", "gpt"]},
            {"skill_id": "langsmith", "category_id": "ai_agentic", "name": "LLM Observability", "years_experience": 1.5, "weight_points": 15, "is_primary": 0, "aliases": ["langsmith", "langfuse", "hivetrace"]},
            {"skill_id": "java", "category_id": "core_backend", "name": "Java", "years_experience": 10.0, "weight_points": 20, "is_primary": 1, "aliases": ["java", "jvm"]},
            {"skill_id": "kotlin", "category_id": "core_backend", "name": "Kotlin", "years_experience": 5.0, "weight_points": 20, "is_primary": 1, "aliases": ["kotlin", "kmp", "kotlin multiplatform"]},
            {"skill_id": "spring_boot", "category_id": "core_backend", "name": "Spring Boot", "years_experience": 8.0, "weight_points": 20, "is_primary": 1, "aliases": ["spring", "spring boot", "spring data", "spring security", "spring ai"]},
            {"skill_id": "ktor", "category_id": "core_backend", "name": "Ktor", "years_experience": 3.0, "weight_points": 15, "is_primary": 0, "aliases": ["ktor"]},
            {"skill_id": "python", "category_id": "secondary_backend", "name": "Python", "years_experience": 4.0, "weight_points": 18, "is_primary": 1, "aliases": ["python"]},
            {"skill_id": "typescript", "category_id": "secondary_backend", "name": "TypeScript / Node.js", "years_experience": 2.0, "weight_points": 9, "is_primary": 0, "aliases": ["typescript", "ts", "node", "nodejs", "node.js"]},
            {"skill_id": "microservices", "category_id": "arch_infra", "name": "Microservices & Distributed Systems", "years_experience": 8.0, "weight_points": 15, "is_primary": 1, "aliases": ["microservices", "distributed systems", "high-load", "high load", "system design"]},
            {"skill_id": "kafka", "category_id": "arch_infra", "name": "Kafka & Event-Driven", "years_experience": 6.0, "weight_points": 15, "is_primary": 1, "aliases": ["kafka", "event-driven", "event driven", "event driven architecture", "rabbitmq"]},
            {"skill_id": "postgresql", "category_id": "arch_infra", "name": "PostgreSQL / SQL", "years_experience": 8.0, "weight_points": 15, "is_primary": 1, "aliases": ["postgresql", "postgres", "sql", "oracle", "mssql"]},
            {"skill_id": "docker_k8s", "category_id": "arch_infra", "name": "Docker & Kubernetes", "years_experience": 6.0, "weight_points": 15, "is_primary": 1, "aliases": ["docker", "kubernetes", "k8s"]},
            {"skill_id": "aws_cloud", "category_id": "arch_infra", "name": "AWS / Cloud Native", "years_experience": 5.0, "weight_points": 15, "is_primary": 1, "aliases": ["aws", "google cloud", "gcp", "cloud architecture", "cloud native"]},
            {"skill_id": "rest_api", "category_id": "arch_infra", "name": "REST & OpenAPI", "years_experience": 8.0, "weight_points": 12, "is_primary": 0, "aliases": ["rest", "rest api", "restful", "openapi", "swagger"]},
            {"skill_id": "fintech", "category_id": "domains", "name": "FinTech & Banking / Payments", "years_experience": 5.0, "weight_points": 10, "is_primary": 1, "aliases": ["fintech", "banking", "payments", "billing", "trading", "brokerage", "financial services", "custody", "enterprise"]},
            {"skill_id": "alien_go", "category_id": "alien", "name": "Golang", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["go", "golang"]},
            {"skill_id": "alien_dotnet", "category_id": "alien", "name": "C# / .NET", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["c#", ".net", "dotnet"]},
            {"skill_id": "alien_cpp", "category_id": "alien", "name": "C++", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["c++"]},
            {"skill_id": "alien_rust", "category_id": "alien", "name": "Rust", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["rust"]},
            {"skill_id": "alien_ruby", "category_id": "alien", "name": "Ruby / Rails", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["ruby", "rails"]},
            {"skill_id": "alien_php", "category_id": "alien", "name": "PHP", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["php"]},
            {"skill_id": "alien_scala", "category_id": "alien", "name": "Scala", "years_experience": 0.0, "weight_points": -20, "is_primary": 0, "aliases": ["scala"]},
            {"skill_id": "legacy_1c", "category_id": "legacy", "name": "1C Enterprise", "years_experience": 0.0, "weight_points": -30, "is_primary": 0, "aliases": ["1c", "1с", "oscript"]},
            {"skill_id": "legacy_sap", "category_id": "legacy", "name": "SAP / ABAP", "years_experience": 0.0, "weight_points": -30, "is_primary": 0, "aliases": ["sap", "abap"]},
            {"skill_id": "legacy_cobol", "category_id": "legacy", "name": "Cobol / Pega / Salesforce", "years_experience": 0.0, "weight_points": -30, "is_primary": 0, "aliases": ["cobol", "salesforce", "mulesoft", "pega"]},
        ],
    }


def get_loaded_skill_matrix(conn: sqlite3.Connection | None = None) -> dict:
    global _SKILL_MATRIX_CACHE
    if _SKILL_MATRIX_CACHE is not None and conn is None:
        return _SKILL_MATRIX_CACHE

    try:
        from main import DB_PATH, get_skill_matrix_data
        should_close = False
        db_conn = conn
        if db_conn is None:
            db_conn = sqlite3.connect(DB_PATH)
            db_conn.row_factory = sqlite3.Row
            should_close = True
        data = get_skill_matrix_data(db_conn)
        if should_close:
            db_conn.close()
        if data and data.get("categories") and data.get("skills"):
            _SKILL_MATRIX_CACHE = data
            return data
    except Exception:
        pass

    return _build_fallback_matrix()


# Множество алиасов по умолчанию (строится автоматически из резервной матрицы)
DEFAULT_CANDIDATE_SKILLS_SET = {
    alias.strip().lower()
    for s in _build_fallback_matrix()["skills"]
    for alias in ([s["name"]] + s.get("aliases", []))
    if alias and alias.strip()
}

NON_PROFILE_TITLE_KEYWORDS = {
    "go", "golang", "react", "angular", "vue", "nextjs", "nuxt", "svelte",
    "frontend", "front-end", "fullstack", "full-stack", "full stack",
    "c#", ".net", "c++", "rust", "php", "ruby", "scala", "elixir", "erlang",
    "swift", "objective-c", "flutter", "react native",
    "django", "fastapi", "laravel", "symfony", "rails",
    "qa", "sdet", "devops", "sre", "secops", "cybersecurity", "threat", "encryption",
    "data engineer", "data scientist", "data analyst", "power bi", "power platform",
    "aem", "apigee", "mulesoft", "salesforce", "sap", "1c", "1с", "drupal", "wordpress", "shopify",
    "revenue operations", "mandarin", "chinese", "pega", "bioinformatics",
}

ARCH_KEYWORDS = {
    "microservices", "distributed systems", "kafka", "spring", "spring boot",
    "event driven", "event-driven", "rest", "openapi", "kubernetes", "k8s", "aws", "docker", "postgresql",
}

FINTECH_KEYWORDS = {"fintech", "payments", "banking", "financial services", "billing", "trading", "brokerage", "enterprise"}


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


def _skill_matches_candidate(skill: str, candidate_aliases: set[str] | None = None) -> bool:
    s = skill.strip().lower()
    if not s:
        return True
    active_set = candidate_aliases if candidate_aliases is not None else DEFAULT_CANDIDATE_SKILLS_SET
    if s in active_set:
        return True
    # Проверка вхождения (например "Spring Boot 3" -> "spring boot", "AWS Lambda" -> "aws")
    for cand in active_set:
        if len(cand) >= 3 and re.search(r"\b" + re.escape(cand) + r"\b", s):
            return True
    return False


def classify_geo_tier(
    title: str,
    description: str,
    enrichment: JobEnrichment,
) -> tuple[bool, str, str | None]:
    """
    Классифицирует вакансию по географическим правилам из SKILL.md (hirify-vacancy-filter):
    - Отсекает жесткие локи на 1 страну (US-only, UK-only, Poland-only, Germany-only, RU-only и т.д. без релокации/B2B).
    - Определяет Tier 1 (Global / Georgia / Anywhere) или Tier 2 (EMEA / Multi-hub / Timezone / Relocation).
    """
    loc_text = " | ".join(
        filter(
            None,
            [
                title,
                " ".join(enrichment.location_restrictions),
                enrichment.remote_policy_detail or "",
                enrichment.work_authorization.summary or "",
                " ".join(enrichment.work_authorization.eligible_regions),
                enrichment.relocation_benefits_detail or "",
            ],
        )
    ).lower()

    full_lower = (loc_text + "\n" + (description or "")[:3000]).lower()
    restrictions_joined = " | ".join(enrichment.location_restrictions).lower()
    remote_low = (enrichment.remote_policy_detail or "").lower()
    fit_summary_low = ((enrichment.resume_fit.summary if enrichment.resume_fit else "") or "").lower()
    has_relocation = enrichment.relocation_assistance == "yes"

    # Сначала проверяем жесткие single-country ограничения, которые извлекла LLM в location_restrictions и remote_policy_detail,
    # потому что в описании может быть маркетинговая фраза про "global company", но нанимают только в 1 стране!
    has_broad_emea = any(
        w in restrictions_joined
        for w in ("emea", "europe", "cet", "utc+", "gmt+", "global", "worldwide", "anywhere", "multi", "georgia")
    )

    single_country_names = (
        "uk", "united kingdom", "great britain", "england", "london",
        "spain", "bulgaria", "poland", "germany", "france", "italy",
        "romania", "ukraine", "portugal", "netherlands", "ireland",
        "hungary", "czech", "austria", "switzerland", "belgium", "sweden",
        "norway", "finland", "denmark", "greece", "lithuania", "latvia", "estonia",
    )
    for country_name in single_country_names:
        if re.search(
            rf"\b{re.escape(country_name)}(?:\s+only|-based|\s+residents?\s+only)\b|\b(?:within|across)\s+(?:the\s+)?{re.escape(country_name)}\b",
            f"{restrictions_joined} | {remote_low}",
        ) and not has_relocation:
            label = f"{country_name.upper()}-only" if country_name == "uk" else f"{country_name.title()}-only"
            return False, f"Rejected: {label}", f"single_country_lock:{label}"

        if not has_broad_emea and not has_relocation:
            if re.search(rf"\b{re.escape(country_name)}\b", restrictions_joined):
                label = f"{country_name.upper()}-only" if country_name == "uk" else f"{country_name.title()}-only"
                return False, f"Rejected: {label}", f"single_country_lock:{label}"

    if re.search(
        r"(?:требует|ограничена)\s+(?:проживания|базирования|локацией)\s+в\s+(?:великобритании|uk|испании|болгарии|польше|германии|франции|сша)",
        fit_summary_low,
    ) and not has_relocation:
        return False, "Rejected: Single-country residency required", "single_country_lock:residency"

    # Если явно разрешены Georgia / Worldwide / Anywhere / Global B2B
    if any(
        kw in full_lower
        for kw in (
            "georgia",
            "tbilisi",
            "work from anywhere",
            "remote worldwide",
            "global remote",
            "anywhere in the world",
        )
    ):
        return True, "Tier 1: Global / Georgia", None

    # Проверка жестких запретов на работу из-за рубежа (US-only, UK-only без визы, single-country EU lock)
    us_lock_patterns = [
        r"remote within the united states",
        r"must live in.*united states",
        r"us citizenship required",
        r"us work authorization required",
        r"united states only",
        r"based in the us\b",
    ]
    for pat in us_lock_patterns:
        if re.search(pat, full_lower):
            return False, "Rejected: US-only", "us_only_lock"

    ru_lock_patterns = [
        r"оформление по тк рф",
        r"только рф",
        r"гражданство рф",
        r"на территории рф",
    ]
    for pat in ru_lock_patterns:
        if re.search(pat, full_lower):
            return False, "Rejected: Russia-only", "ru_only_lock"

    # Проверка жестких ограничений по типу контракта (против B2B / Contractor из Грузии, согласно preferences.md)
    contract_locks = [
        (r"\bw-?2 only\b|\bno c2c\b|\bno corp-to-corp\b", "W2-only (No B2B/C2C)"),
        (r"\binside ir35\b", "UK Inside IR35"),
        (r"\bpaye only\b", "UK PAYE-only (No B2B)"),
        (r"\bno b2b\b|\bno contractors\b", "No B2B / Contractors"),
    ]
    for pat, label in contract_locks:
        if re.search(pat, full_lower):
            return False, f"Rejected: {label}", f"contract_lock:{label}"

    # Проверка single-country lock в location_restrictions (если нет relocation и нет EMEA/Global)
    restrictions_joined = " | ".join(enrichment.location_restrictions).lower()
    remote_low = (enrichment.remote_policy_detail or "").lower()
    fit_summary_low = ((enrichment.resume_fit.summary if enrichment.resume_fit else "") or "").lower()

    has_broad_emea = any(
        w in restrictions_joined
        for w in ("emea", "europe", "cet", "utc+", "gmt+", "global", "worldwide", "anywhere", "multi", "georgia")
    )
    has_relocation = enrichment.relocation_assistance == "yes"

    # Если LLM в location_restrictions явно поставила одну страну без EMEA/Europe/Global (например ['Bulgaria'], ['UK only'], ['Spain only'], ['UK-based'])
    single_country_names = (
        "uk", "united kingdom", "great britain", "england", "london",
        "spain", "bulgaria", "poland", "germany", "france", "italy",
        "romania", "ukraine", "portugal", "netherlands", "ireland",
        "hungary", "czech", "austria", "switzerland", "belgium", "sweden",
        "norway", "finland", "denmark", "greece", "lithuania", "latvia", "estonia",
    )
    for country_name in single_country_names:
        # 1) Если в location_restrictions или remote_policy написано "<country> only" / "within <country>" / "<country>-based"
        if re.search(
            rf"\b{re.escape(country_name)}(?:\s+only|-based|\s+residents?\s+only)\b|\b(?:within|across)\s+(?:the\s+)?{re.escape(country_name)}\b",
            f"{restrictions_joined} | {remote_low}",
        ) and not has_relocation:
            label = f"{country_name.upper()}-only" if country_name == "uk" else f"{country_name.title()}-only"
            return False, f"Rejected: {label}", f"single_country_lock:{label}"

        # 2) Если в location_restrictions указана только эта страна (и нет широкого EMEA/Europe/Worldwide)
        if not has_broad_emea and not has_relocation:
            if re.search(rf"\b{re.escape(country_name)}\b", restrictions_joined):
                label = f"{country_name.upper()}-only" if country_name == "uk" else f"{country_name.title()}-only"
                return False, f"Rejected: {label}", f"single_country_lock:{label}"

    # 3) Если сама LLM в resume_fit.summary прямо написала, что роль требует проживания/базирования в одной стране (UK, Испании, Болгарии и т.д.)
    if re.search(
        r"(?:требует|ограничена)\s+(?:проживания|базирования|локацией)\s+в\s+(?:великобритании|uk|испании|болгарии|польше|германии|франции|сша)",
        fit_summary_low,
    ) and not has_relocation:
        return False, "Rejected: Single-country residency required", "single_country_lock:residency"

    single_country_locks = [
        (r"\b(?:uk|united kingdom) only\b", "UK-only"),
        (r"\bmust (?:reside|live|be based|be located) in (?:the )?(?:uk|united kingdom)\b", "UK-only"),
        (r"\bsc eligible\b", "UK Security Clearance required"),
        (r"\bsecurity clearance\b", "Security Clearance required"),
        (r"\bpoland only\b|\bmust (?:reside|live|be based) in poland\b", "Poland-only"),
        (r"\bgermany only\b|\bmust (?:reside|live|be based) in germany\b", "Germany-only"),
        (r"\bfrance only\b|\bmust (?:reside|live|be based) in france\b", "France-only"),
        (r"\bspain only\b|\bmust (?:reside|live|be based) in spain\b", "Spain-only"),
        (r"\bitaly only\b|\bmust (?:reside|live|be based) in italy\b", "Italy-only"),
        (r"\bromania only\b|\bmust (?:reside|live|be based) in romania\b", "Romania-only"),
        (r"\bukraine only\b|\bmust (?:reside|live|be based) in ukraine\b", "Ukraine-only"),
    ]
    for pat, label in single_country_locks:
        if re.search(pat, full_lower) and not has_relocation:
            return False, f"Rejected: {label}", f"single_country_lock:{label}"

    # Если в заголовке жестко указан 1 город/страна без слова EMEA/Europe/Worldwide (например "(Milan)", "(Iasi)", "Perm - London")
    if not has_broad_emea and not has_relocation:
        if re.search(r"\b(?:uk|united kingdom|london|poland|germany|france|spain|italy|netherlands|ireland)\s+only\b", restrictions_joined):
            return False, f"Rejected: {enrichment.location_restrictions}", "single_country_restriction"

    # Проверка требования немецкого/французского/польского языка на уровне C1/Native
    for lang in enrichment.required_languages:
        l_low = lang.lower()
        if any(fl in l_low for fl in ("german", "french", "spanish", "polish", "italian", "dutch")) and not any(
            a1 in l_low for a1 in ("a1", "a2", "basic")
        ):
            return False, f"Rejected: Language ({lang})", f"required_language:{lang}"

    if any(w in restrictions_joined for w in ("worldwide", "global", "anywhere")):
        return True, "Tier 1: Global / Georgia", None

    return True, "Tier 2: EMEA / Multi-hub", None


def score_vacancy_by_skill(
    title: str,
    company: str | None,
    date_posted: str | None,
    seniority_level: str | None,
    industry: str | None,
    salary_text: str | None,
    description: str,
    enrichment: JobEnrichment,
    conn: sqlite3.Connection | None = None,
) -> SkillScoreResult:
    """
    Полная реализация скоринговой модели (0..100 баллов) из SKILL.md (hirify-vacancy-filter)
    с динамической загрузкой весов, категорий и навыков из БД (jobs.db).
    """
    geo_passed, tier, geo_reason = classify_geo_tier(title, description, enrichment)

    matrix = get_loaded_skill_matrix(conn)
    categories = matrix.get("categories", [])
    skills = matrix.get("skills", [])

    # Группировка навыков по категориям
    skills_by_cat: dict[str, list[dict]] = {}
    for s in skills:
        skills_by_cat.setdefault(s["category_id"], []).append(s)

    # Формируем множество алиасов кандидата (из категорий с неотрицательным множителем)
    candidate_aliases: set[str] = set()
    for cat in categories:
        if float(cat.get("multiplier", 1.0)) >= 0:
            for s in skills_by_cat.get(cat["category_id"], []):
                candidate_aliases.add(s["name"].strip().lower())
                for a in s.get("aliases", []):
                    if a and a.strip():
                        candidate_aliases.add(a.strip().lower())

    if not candidate_aliases:
        candidate_aliases = DEFAULT_CANDIDATE_SKILLS_SET

    all_job_tech = [t.strip().lower() for t in enrichment.required_technologies if t.strip()]
    nice_tech = [t.strip().lower() for t in enrichment.nice_to_have_technologies if t.strip()]
    combined_tech_and_title = " ".join([title.lower(), *all_job_tech, *nice_tech])
    desc_lower = (description or "").lower()

    matched_skills: list[str] = []
    missing_skills: list[str] = []

    for tech in enrichment.required_technologies:
        t_low = tech.strip().lower()
        if not t_low:
            continue
        if _skill_matches_candidate(t_low, candidate_aliases):
            if t_low not in matched_skills:
                matched_skills.append(t_low)
        else:
            if t_low not in missing_skills:
                missing_skills.append(t_low)

    # Дополняем из nice_to_have совпавшие навыки
    for tech in enrichment.nice_to_have_technologies:
        t_low = tech.strip().lower()
        if t_low and _skill_matches_candidate(t_low, candidate_aliases) and t_low not in matched_skills:
            matched_skills.append(t_low)

    score = 0
    breakdown: list[str] = []

    # 1. Tech Stack, Specialization & Architecture Match (динамически по категориям из БД)
    matched_skill_ids: set[str] = set()
    for s in skills:
        sid = s["skill_id"]
        aliases = [s["name"].lower()] + [a.lower() for a in s.get("aliases", []) if a]
        found = False
        for a in aliases:
            if not a:
                continue
            if len(a) <= 3:
                if re.search(r"\b" + re.escape(a) + r"\b", combined_tech_and_title) or re.search(r"\b" + re.escape(a) + r"\b", desc_lower[:3000]):
                    found = True
                    break
            else:
                if a in combined_tech_and_title or a in desc_lower[:3000]:
                    found = True
                    break
        if found:
            matched_skill_ids.add(sid)

    has_core_language = any(sid in matched_skill_ids for sid in ("java", "kotlin", "spring_boot"))
    has_python = "python" in matched_skill_ids
    has_agentic = any(s["category_id"] == "ai_agentic" for s in skills if s["skill_id"] in matched_skill_ids)

    for cat in sorted(categories, key=lambda c: c.get("sort_order", 0)):
        cid = cat["category_id"]
        ctitle = cat["title"]
        cmult = float(cat.get("multiplier", 1.0))
        cmax = int(cat.get("max_points", 0))
        cat_skills = skills_by_cat.get(cid, [])
        cat_matched = [s for s in cat_skills if s["skill_id"] in matched_skill_ids]

        if cmult < 0 or cmax < 0:
            penalty = cmax if cmax < 0 else -abs(cmax)
            if cid == "alien" or "alien" in cid:
                # Чужой стек применяется, только если вакансия не содержит основной стек (Java/Kotlin/Python/AI)
                if cat_matched and not (has_core_language or has_python or has_agentic):
                    score += penalty
                    breakdown.append(f"{ctitle} ({penalty})")
            elif cid == "legacy" or "legacy" in cid:
                if cat_matched:
                    score += penalty
                    breakdown.append(f"{ctitle} ({penalty})")
            else:
                if cat_matched:
                    score += penalty
                    breakdown.append(f"{ctitle} ({penalty})")
        else:
            if not cat_matched:
                continue

            if cid in ("ai_agentic", "core_backend", "secondary_backend"):
                if cid == "secondary_backend" and has_core_language and not has_python:
                    continue
                best_pts = max((s.get("weight_points", 0) for s in cat_matched), default=0)
                earned = min(best_pts, cmax) if cmax > 0 else best_pts
            elif cid == "arch_infra":
                if len(cat_matched) >= 3:
                    earned = min(15, cmax)
                elif len(cat_matched) >= 1:
                    earned = min(10, cmax)
                else:
                    earned = 0
            elif cid == "domains":
                best_pts = max((s.get("weight_points", 0) for s in cat_matched), default=0)
                earned = min(best_pts, cmax) if cmax > 0 else best_pts
            else:
                sum_pts = sum(s.get("weight_points", 0) for s in cat_matched)
                earned = min(sum_pts, cmax) if cmax > 0 else sum_pts

            if earned > 0:
                score += earned
                breakdown.append(f"{ctitle} (+{earned})")

    # 2. Seniority / Grade Fit (0 to 15 pts)
    title_low = title.lower()
    sen_low = (seniority_level or "").lower()
    if any(w in title_low for w in ("intern", "junior")) or sen_low in ("internship", "entry level"):
        score -= 20
        breakdown.append("Junior/Entry (-20)")
    elif any(w in title_low for w in ("lead", "team lead", "tech lead")):
        score += 5
        breakdown.append("Lead (+5)")
    elif any(w in title_low for w in ("senior", "sr.", "sr ", "staff", "principal", "architect")) or "mid-senior" in sen_low:
        score += 15
        breakdown.append("Senior/Staff (+15)")
    else:
        score += 8
        breakdown.append("Mid/Regular (+8)")

    # 3. Location & Format Match (0 to 15 pts)
    if tier.startswith("Tier 1"):
        score += 15
        breakdown.append("Tier 1 Global/Georgia (+15)")
    elif tier.startswith("Tier 2"):
        score += 10
        breakdown.append("Tier 2 EMEA/Europe (+10)")

    # 4. Salary Match vs preferences.md ($6,000 - $8,000/mo or $72,000 - $96,000/yr)
    if salary_text:
        nums = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", salary_text)]
        max_num = max(nums) if nums else 0
        # Конвертация GBP/EUR в USD приблизительно для оценки порога $72k/yr ($6k/mo)
        mult = 1.28 if "£" in salary_text or "gbp" in salary_text.lower() else (1.08 if "€" in salary_text or "eur" in salary_text.lower() else 1.0)
        adj_max = max_num * mult

        if adj_max >= 72000 or (1000 <= adj_max < 25000 and adj_max >= 6000 and "/mo" in salary_text.lower()):
            score += 10
            breakdown.append(f"Salary {salary_text} >= $6k/mo (+10)")
        elif adj_max >= 55000 or (1000 <= adj_max < 25000 and adj_max >= 4500 and "/mo" in salary_text.lower()):
            score += 5
            breakdown.append(f"Salary {salary_text} (+5)")
        elif adj_max >= 1000:
            breakdown.append(f"Salary below $6k/mo target: {salary_text} (+0)")
        else:
            score += 5
            breakdown.append(f"Salary {salary_text} (+5)")
    else:
        score += 5
        breakdown.append("Salary unstated (+5)")

    # 5. Freshness (+5 pts)
    score += 5
    breakdown.append("Fresh (+5)")

    # 6. Missing Skills Penalty (-3 pts per missing required skill)
    if missing_skills:
        pen = len(missing_skills) * 3
        score -= pen
        breakdown.append(f"Пробелы в стеке: {len(missing_skills)} навыка (-{pen})")

    # 7. Title Skill Mismatch Penalty (Непрофильный навык / специализация в заголовке: -20 pts и потолок <= 68)
    title_penalty_tokens: list[str] = []
    for kw in NON_PROFILE_TITLE_KEYWORDS:
        if re.search(r"(?:^|[\s\(/,-])" + re.escape(kw) + r"(?:$|[\s\)/,-])", title_low):
            title_penalty_tokens.append(kw)
    for miss in missing_skills:
        if len(miss) >= 2 and re.search(r"\b" + re.escape(miss) + r"\b", title_low):
            if miss not in title_penalty_tokens:
                title_penalty_tokens.append(miss)

    has_clean_title = len(title_penalty_tokens) == 0
    if not has_clean_title:
        score -= 20
        breakdown.append(f"Непрофильный заголовок [{', '.join(title_penalty_tokens)}] (-20, cap ≤68)")
        if score > 68:
            score = 68

    score = max(0, min(100, score))

    if not geo_passed:
        match_category = "rejected_geo"
    elif score >= 70:
        match_category = "top"
    elif score >= 50:
        match_category = "good"
    else:
        match_category = "low"

    return SkillScoreResult(
        score=score,
        tier=tier,
        geo_passed=geo_passed,
        geo_reject_reason=geo_reason,
        has_clean_title=has_clean_title,
        title_penalty_tokens=title_penalty_tokens,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        breakdown=breakdown,
        match_category=match_category,
    )

