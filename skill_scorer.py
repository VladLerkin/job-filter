import re
from datetime import date, datetime
from pydantic import BaseModel, Field

from enrichment_schema import JobEnrichment

# Профиль кандидата из hirify-filter-bot-export-skill
CANDIDATE_SKILLS_SET = {
    # Languages
    "java", "kotlin", "python", "typescript", "sql", "node", "nodejs", "node.js",
    # Frameworks & Backend
    "spring", "spring boot", "spring data", "spring security", "spring ai", "ktor", "quartz", "kmp", "kotlin multiplatform",
    # AI & Agentic Systems
    "ai", "ai engineer", "ai engineering", "ai agentic", "ai agentic engineer", "ai agents", "agentic", "agentic ai",
    "multi-agent", "multi agent", "rag", "mem0", "memsearch", "mcp", "a2a", "agent-to-agent",
    "langsmith", "langfuse", "hivetrace", "agent security", "local llm", "llm", "llms", "agents", "prompt engineering", "genai", "generative ai",
    "langgraph", "langchain", "crewai", "koog", "machine learning", "claude", "openai", "anthropic", "gpt", "embeddings", "vector db",
    # Architecture & Protocols
    "microservices", "rest", "rest api", "restful", "apis", "api", "http", "http api", "openapi", "swagger",
    "event-driven", "event driven", "event driven architecture",
    "high-load", "high load", "high load systems", "distributed systems", "software architecture", "system design", "cloud architecture", "cloud native",
    # Databases & Storage
    "postgresql", "postgres", "oracle", "oracle db", "mssql", "sql server", "s3", "s3 storage", "storage", "databases",
    # DevOps & Cloud
    "docker", "kubernetes", "k8s", "aws", "google cloud", "gcp", "gitlab", "gitlab ci", "gitlab ci/cd", "ci cd", "ci/cd", "github", "gradle", "maven", "git",
    # Domains & Business Systems
    "fintech", "banking", "custody", "brokerage", "payments", "billing", "ecm", "crm", "bpm", "erp", "healthcare", "medtech", "travel",
    # General engineering & message brokers
    "backend", "backend engineering", "backend development", "software engineering", "clean code", "clean architecture", "architecture", "solution architecture",
    "kafka", "rabbitmq", "testing", "automation",
}

ALIEN_LANGS = {"go", "golang", "c#", ".net", "c++", "rust", "ruby", "php", "elixir", "scala", "swift", "objective-c"}

AGENTIC_SPECIALTY_KEYWORDS = {
    "agentic", "agentic ai", "ai agentic", "ai agents", "agents", "multi-agent", "multi agent",
    "llm", "llms", "rag", "mcp", "a2a", "langgraph", "langchain", "crewai", "koog", "prompt engineering",
    "ai-инженер", "ai engineer", "ai developer", "applied ai", "genai engineer",
}

AI_KEYWORDS = {
    "ai", "genai", "generative ai", "llm", "llms", "agentic", "rag", "mcp", "agents",
    "langgraph", "langchain", "crewai", "prompt engineering", "machine learning",
}

LEGACY_KEYWORDS = {"1c", "1с", "oscript", "sap", "cobol", "salesforce", "mulesoft", "duck creek", "abap", "pega"}

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


def _skill_matches_candidate(skill: str) -> bool:
    s = skill.strip().lower()
    if not s:
        return True
    if s in CANDIDATE_SKILLS_SET:
        return True
    # Проверка вхождения (например "Spring Boot 3" -> "spring boot", "AWS Lambda" -> "aws")
    for cand in CANDIDATE_SKILLS_SET:
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
) -> SkillScoreResult:
    """
    Полная реализация скоринговой модели (0..100 баллов) из SKILL.md (hirify-vacancy-filter).
    """
    geo_passed, tier, geo_reason = classify_geo_tier(title, description, enrichment)

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
        if _skill_matches_candidate(t_low):
            if t_low not in matched_skills:
                matched_skills.append(t_low)
        else:
            if t_low not in missing_skills:
                missing_skills.append(t_low)

    # Дополняем из nice_to_have совпавшие навыки
    for tech in enrichment.nice_to_have_technologies:
        t_low = tech.strip().lower()
        if t_low and _skill_matches_candidate(t_low) and t_low not in matched_skills:
            matched_skills.append(t_low)

    score = 0
    breakdown: list[str] = []

    # 1. Tech Stack, Specialization & Architecture Match
    has_agentic = any(kw in combined_tech_and_title or kw in desc_lower[:2500] for kw in AGENTIC_SPECIALTY_KEYWORDS)
    has_general_ai = any(kw in combined_tech_and_title for kw in AI_KEYWORDS)

    if has_agentic:
        score += 30
        breakdown.append("AI Agentic Specialty (+30)")
    elif has_general_ai:
        score += 15
        breakdown.append("General AI (+15)")

    # Core languages: Java / Kotlin (+20), Python (+18), TypeScript (+9)
    has_java_kotlin = any(
        re.search(r"\b(?:java|kotlin|jvm|spring)\b", s) for s in [title.lower(), *all_job_tech]
    )
    has_python = any("python" in s for s in [title.lower(), *all_job_tech])
    has_ts = any(s in ("typescript", "ts", "node.js", "nodejs") for s in all_job_tech) or "typescript" in title.lower()

    if has_java_kotlin:
        score += 20
        breakdown.append("Java/Kotlin (+20)")
    if has_python:
        score += 18
        breakdown.append("Python (+18)")
    elif has_ts and not has_java_kotlin:
        score += 9
        breakdown.append("TypeScript/Node (+9)")

    # Alien backend languages without candidate languages or AI: -20 pts
    has_alien = any(al in all_job_tech for al in ALIEN_LANGS)
    if has_alien and not (has_java_kotlin or has_python or has_agentic):
        score -= 20
        breakdown.append("Alien Stack Penalty (-20)")

    # Architecture & Infrastructure (+8 to +15)
    arch_hits = sum(1 for kw in ARCH_KEYWORDS if kw in combined_tech_and_title or kw in desc_lower)
    if arch_hits >= 3:
        score += 15
        breakdown.append("Arch/Microservices (+15)")
    elif arch_hits >= 1:
        score += 10
        breakdown.append("Arch/Microservices (+10)")

    # Domain: FinTech / Payments / Banking / Enterprise (+10)
    ind_and_desc = f"{(industry or '').lower()} {desc_lower[:1500]}"
    if any(fk in ind_and_desc for fk in FINTECH_KEYWORDS):
        score += 10
        breakdown.append("FinTech/Enterprise (+10)")

    # Legacy penalty (-30)
    if any(lk in combined_tech_and_title for lk in LEGACY_KEYWORDS):
        score -= 30
        breakdown.append("Legacy/Irrelevant Stack (-30)")

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

