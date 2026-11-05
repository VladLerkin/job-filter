"""Скоринг вакансии (0..100 баллов) по стеку технологий, уровню, локации, зарплате и свежести."""
import re
import sqlite3

from job_filter import config
from job_filter.models.enrichment import JobEnrichment
from job_filter.models.scoring import SkillScoreResult
from job_filter.scoring.geo import classify_geo_tier
from job_filter.scoring.matrix import (
    extract_candidate_aliases,
    get_skill_matrix,
    skill_matches_candidate,
)

NON_PROFILE_TITLE_KEYWORDS = tuple(sorted([
    "go", "golang", "react", "angular", "vue", "nextjs", "nuxt", "svelte",
    "frontend", "front-end", "fullstack", "full-stack", "full stack",
    "c#", ".net", "c++", "rust", "php", "ruby", "scala", "elixir", "erlang",
    "swift", "objective-c", "flutter", "react native",
    "django", "fastapi", "laravel", "symfony", "rails",
    "qa", "sdet", "devops", "sre", "secops", "cybersecurity", "threat", "encryption",
    "data engineer", "data scientist", "data analyst", "power bi", "power platform",
    "aem", "apigee", "mulesoft", "salesforce", "sap", "1c", "1с", "drupal", "wordpress", "shopify",
    "revenue operations", "mandarin", "chinese", "pega", "bioinformatics",
]))


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
    matrix: dict | None = None,
    geo_preferences: dict | None = None,
) -> SkillScoreResult:
    """
    Полная реализация скоринговой модели (0..100 баллов) с динамической загрузкой весов,
    категорий и навыков из БД или переданной матрицы.
    """
    if geo_preferences is None and conn is not None:
        try:
            from job_filter.repositories import candidate_repo
            settings = candidate_repo.get_settings(conn)
            geo_preferences = settings.get("geo_preferences")
        except Exception:
            pass

    geo_passed, tier, geo_reason = classify_geo_tier(title, description, enrichment, geo_preferences=geo_preferences)

    if matrix is None:
        matrix = get_skill_matrix(conn)
    categories = matrix.get("categories", [])
    skills = matrix.get("skills", [])

    skills_by_cat: dict[str, list[dict]] = {}
    for s in skills:
        skills_by_cat.setdefault(s["category_id"], []).append(s)

    candidate_aliases = extract_candidate_aliases(matrix)

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
        if skill_matches_candidate(t_low, candidate_aliases):
            if t_low not in matched_skills:
                matched_skills.append(t_low)
        else:
            if t_low not in missing_skills:
                missing_skills.append(t_low)

    for tech in enrichment.nice_to_have_technologies:
        t_low = tech.strip().lower()
        if t_low and skill_matches_candidate(t_low, candidate_aliases) and t_low not in matched_skills:
            matched_skills.append(t_low)

    score = 0
    breakdown: list[str] = []

    # 1. Tech Stack, Specialization & Architecture Match
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

    # 3. Location & Format Match (0 to 20 pts)
    if tier.startswith("Tier 1A"):
        score += 20
        breakdown.append("Tier 1A Local/Georgia (+20)")
    elif tier.startswith("Tier 1B") or tier.startswith("Tier 1"):
        score += 18
        breakdown.append("Tier 1B True Global Remote (+18)")
    elif tier.startswith("Tier 2A"):
        score += 12
        breakdown.append("Tier 2A Broad EMEA / Timezone (+12)")
    elif tier.startswith("Tier 2B"):
        score += 10
        breakdown.append(f"{tier} (+10)")
    elif tier.startswith("Tier 2"):
        score += 10
        breakdown.append("Tier 2 EMEA/Europe (+10)")

    # 4. Salary Match vs target ($6k-$8k/mo)
    if salary_text:
        nums = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", salary_text)]
        max_num = max(nums) if nums else 0
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

    # 7. Title Skill Mismatch Penalty
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
    elif score >= config.TOP_SCORE_THRESHOLD:
        match_category = "top"
    elif score >= config.GOOD_SCORE_THRESHOLD:
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
