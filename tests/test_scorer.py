"""Тесты скоринга вакансий и гео-классификации."""
from job_filter.db.seed_data import default_skill_matrix
from job_filter.models.enrichment import JobEnrichment, ResumeFit, WorkAuthorization
from job_filter.scoring.geo import classify_geo_tier
from job_filter.scoring.scorer import score_vacancy_by_skill


def test_classify_geo_tier_us_only():
    enr = JobEnrichment(
        location_restrictions=["United States only"],
        work_authorization=WorkAuthorization(summary="US citizenship required"),
    )
    passed, tier, reason = classify_geo_tier("Software Engineer", "Remote in US", enr)
    assert passed is False
    assert "US-only" in tier or "United States" in tier


def test_classify_geo_tier_global():
    enr = JobEnrichment(
        location_restrictions=["Worldwide", "Global"],
        remote_policy_detail="Work from anywhere in the world",
    )
    passed, tier, reason = classify_geo_tier("AI Engineer", "Remote worldwide", enr)
    assert passed is True
    assert "Tier 1" in tier


def test_classify_geo_tier_local_georgia():
    enr = JobEnrichment(
        location_restrictions=["Georgia", "Eastern Europe"],
        remote_policy_detail="Remote within Georgia / Caucasus / Eastern Europe",
    )
    passed, tier, reason = classify_geo_tier("Senior Backend Engineer", "Remote Georgia", enr)
    assert passed is True
    assert "Tier 1A" in tier


def test_classify_geo_tier_country_lock_with_relocation():
    enr = JobEnrichment(
        location_restrictions=["Germany only"],
        relocation_assistance="yes",
        relocation_benefits_detail="Visa sponsorship and relocation package provided",
    )
    passed, tier, reason = classify_geo_tier("Backend Lead", "Based in Berlin with visa support", enr)
    assert passed is True
    assert "Tier 2B" in tier
    assert "Relocation" in tier


def test_classify_geo_tier_country_lock_no_relocation():
    enr = JobEnrichment(
        location_restrictions=["Germany only"],
        relocation_assistance="no",
        remote_policy_detail="Must reside in Germany",
    )
    passed, tier, reason = classify_geo_tier("Backend Engineer", "Germany remote", enr)
    assert passed is False
    assert "single_country_lock" in (reason or "")


def test_score_vacancy_top_match():
    enr = JobEnrichment(
        location_restrictions=["Worldwide"],
        required_technologies=["Java", "Spring Boot", "Kafka", "PostgreSQL"],
        nice_to_have_technologies=["Docker", "Kubernetes"],
        resume_fit=ResumeFit(score=90),
    )
    res = score_vacancy_by_skill(
        title="Senior Java / Spring Boot Engineer",
        company="TechCorp",
        date_posted="2026-10-25",
        seniority_level="Senior",
        industry="Financial Services",
        salary_text="$8,000/mo",
        description="Senior Java backend engineer needed for microservices.",
        enrichment=enr,
        matrix=default_skill_matrix(),
    )
    assert res.geo_passed is True
    assert res.score >= 70
    assert res.match_category == "top"
    assert res.has_clean_title is True


def test_classify_geo_tier_us_city_state_does_not_match_georgia():
    enr = JobEnrichment(
        location_restrictions=["Remote; San Ramon, CA", "EMEA"],
        remote_policy_detail="Remote; San Ramon, CA / EMEA",
        work_authorization=WorkAuthorization(summary="Remote role based in US. 401(k) match."),
    )
    passed, tier, reason = classify_geo_tier(
        "AI Engineer II (AI Security)",
        "Location: Remote; San Ramon, CA\nAnnual salary: $85,000–$124,000\n401(k) savings plan",
        enr,
        job_location="usa (United States)",
    )
    assert passed is False
    assert tier == "Rejected: US-only"
    assert reason == "us_only_lock"


def test_classify_geo_tier_ineligible_clause_not_matching_georgia():
    enr = JobEnrichment(
        location_restrictions=["Mexico only (Ineligible for remote from Georgia, Tbilisi)"],
        remote_policy_detail="Teleworker position; employees may live anywhere in Mexico.",
    )
    passed, tier, reason = classify_geo_tier(
        "Senior Software Development Engineer",
        "Employees may live anywhere in Mexico",
        enr,
        job_location="Remote (Mexico)",
    )
    assert passed is False
    assert "Mexico-only" in tier
    assert "single_country_lock" in (reason or "")


def test_classify_geo_tier_country_pool_no_relocation():
    enr = JobEnrichment(
        location_restrictions=["Czech Republic", "Slovakia", "Hungary"],
        remote_policy_detail="Fully remote from Czechia, Slovakia or Hungary (full-time B2B engagement)",
        work_authorization=WorkAuthorization(
            summary="Fully remote role restricted to residents/tax residents in Czechia, Slovakia, or Hungary via B2B.",
            eligible_regions=["Czech Republic", "Slovakia", "Hungary"],
        ),
        resume_fit=ResumeFit(
            summary="Отличный стек Java/Kotlin, но вакансия строго ограничена ремоутом из Чехии, Словакии или Венгрии без релокации."
        ),
        relocation_assistance="unclear",
    )
    passed, tier, reason = classify_geo_tier(
        "Senior Backend Developer (Java/Kotlin)",
        "Fully remote from Czechia, Slovakia or Hungary",
        enr,
        job_location="europe (Czech Republic, Hungary, Slovakia)",
    )
    assert passed is False
    assert "Restricted countries" in tier
    assert "Czechia" in tier
    assert "Hungary" in tier
    assert "Slovakia" in tier
    assert "country_pool_lock" in (reason or "")


def test_classify_geo_tier_country_pool_with_relocation():
    enr = JobEnrichment(
        location_restrictions=["Czech Republic", "Slovakia", "Hungary"],
        relocation_assistance="yes",
        relocation_benefits_detail="Relocation package provided",
    )
    passed, tier, reason = classify_geo_tier(
        "Senior Backend Developer",
        "Relocation offered to Prague",
        enr,
        job_location="europe (Czech Republic, Hungary, Slovakia)",
    )
    assert passed is True
    assert "Tier 2B" in tier
    assert "Relocation" in tier


def test_classify_geo_tier_country_pool_with_georgia_included():
    enr = JobEnrichment(
        location_restrictions=["Poland", "Georgia", "Romania"],
        remote_policy_detail="Remote from Poland, Georgia, Romania",
    )
    passed, tier, reason = classify_geo_tier(
        "Senior Java Engineer",
        "Hiring in Poland, Georgia or Romania",
        enr,
        job_location="europe (Poland, Georgia, Romania)",
    )
    assert passed is True
    assert "Tier 1A" in tier


def test_classify_geo_tier_eu_only_no_relocation():
    enr = JobEnrichment(
        location_restrictions=["EU only"],
        remote_policy_detail="Remote within EU/EEA only",
    )
    passed, tier, reason = classify_geo_tier(
        "Platform Engineer",
        "Must be located in the EU",
        enr,
        job_location="Europe",
    )
    assert passed is False
    assert "EU-only" in tier


def test_classify_geo_tier_temp_wfa_perk_does_not_make_global():
    enr = JobEnrichment(
        location_restrictions=["Brazil"],
        remote_policy_detail="Remote-first within Brazil, with the option to work from São Paulo office; Work From Anywhere up to 90 days/year",
        work_authorization=WorkAuthorization(
            summary="Remote-first within Brazil; requires location/work authorization in Brazil.",
            eligible_regions=["Brazil"],
        ),
        required_languages=["Portuguese (Fluent)", "English (Excellent)"],
    )
    passed, tier, reason = classify_geo_tier(
        "Staff Software Engineer - Frameworks",
        "Work From Anywhere up to 90 days/year. Must reside in Brazil.",
        enr,
        job_location="Remote (Brazil)",
    )
    assert passed is False
    assert "Brazil-only" in tier or "Language" in tier


def test_classify_geo_tier_wfa_across_single_country_not_global():
    enr = JobEnrichment(
        location_restrictions=["Japan"],
        remote_policy_detail="Full Remote / Flextime & Hybrid Work; can work from anywhere across Japan (offices or home)",
        required_languages=["Japanese (Business)", "English"],
    )
    passed, tier, reason = classify_geo_tier(
        "Product Engineer",
        "can work from anywhere across Japan",
        enr,
        job_location="Tokyo, Japan",
    )
    assert passed is False
    assert "Japan-only" in tier or "Language" in tier



