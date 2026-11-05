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

