"""Тесты для адаптера FreeHire и роутера /api/freehire."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from job_filter.api.app import create_app
from job_filter.scraping.freehire_adapter import (
    DEFAULT_FREEHIRE_FACETS,
    DF_COLS,
    FreeHireClient,
    build_freehire_query_params,
    map_blacklisted_domains_to_freehire_sources,
    match_profile_skills_to_freehire,
    scrape_freehire,
)


def test_build_freehire_query_params_serialization():
    params = build_freehire_query_params(
        {
            "ai_archetype": ["agent_builder", "rag_app_builder"],
            "category": ["ai_engineering", "backend"],
            "work_mode": ["remote"],
            "work_mode_remote_anywhere": True,
            "skills": ["python", "rag"],
            "skills_mode": "and",
            "via_recruiter": False,
            "requires_clearance": False,
            "q": "langgraph",
        },
        extra_source_exclude=["workday", "taleo"],
    )
    assert params["ai_archetype"] == "agent_builder,rag_app_builder"
    assert params["category"] == "ai_engineering,backend"
    assert params["work_mode"] == "remote"
    assert params["work_mode_remote_anywhere"] == "true"
    assert params["skills"] == "python,rag"
    assert params["skills_mode"] == "and"
    assert params["via_recruiter"] == "false"
    assert params["requires_clearance"] == "false"
    assert params["source_exclude"] == "taleo,workday"
    assert params["q"] == "langgraph"


def test_build_freehire_query_params_omits_or_skills_mode():
    params = build_freehire_query_params({"skills": ["python"], "skills_mode": "or", "q": "   "})
    assert "skills_mode" not in params
    assert "q" not in params


def test_map_blacklisted_domains_to_freehire_sources():
    domains = ["wd5.myworkdayjobs.com", "taleo.net", "careers.icims.com", "random-company.com"]
    mapped = map_blacklisted_domains_to_freehire_sources(domains)
    assert mapped == ["icims", "taleo", "workday"]


def test_match_profile_skills_to_freehire():
    aliases = {"Python", "Agentic AI", "Spring Boot", "UnknownTool123", "RAG"}
    available = {
        "python": 310000,
        "agentic-ai": 5200,
        "spring-boot": 42000,
        "rag": 18000,
        "react": 200000,
    }
    matched = match_profile_skills_to_freehire(aliases, available)
    slugs = [m["slug"] for m in matched]
    assert slugs == ["python", "spring-boot", "rag", "agentic-ai"]


def test_scrape_freehire_mapping_and_filtering():
    now = datetime.now(timezone.utc)
    recent_iso = (now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    old_iso = (now - timedelta(hours=100)).isoformat().replace("+00:00", "Z")

    mock_client = MagicMock(spec=FreeHireClient)
    mock_client.search_jobs.return_value = {
        "meta": {"total": 3, "limit": 50, "offset": 0},
        "data": [
            {
                "public_slug": "senior-ai-engineer-acme-123",
                "url": "https://boards.greenhouse.io/acme/jobs/123?utm_source=freehire.me",
                "title": "Senior AI Agent Engineer",
                "company": "Acme AI",
                "location": "Europe",
                "work_mode": "remote",
                "regions": ["eu"],
                "countries": ["de"],
                "description": "# Role\nBuild autonomous AI agents with Python and LangGraph.",
                "posted_at": recent_iso,
                "enrichment": {
                    "seniority": "senior",
                    "employment_type": "full_time",
                    "salary_min": 140000,
                    "salary_max": 180000,
                    "salary_currency": "USD",
                    "salary_period": "year",
                },
            },
            {
                "public_slug": "already-processed-slug",
                "url": "https://jobs.lever.co/foo/456",
                "title": "Already Seen",
                "company": "Foo",
                "work_mode": "remote",
                "description": "Skip me",
                "posted_at": recent_iso,
                "enrichment": {},
            },
            {
                "public_slug": "too-old-slug",
                "url": "https://jobs.lever.co/bar/789",
                "title": "Old Job",
                "company": "Bar",
                "work_mode": "remote",
                "description": "Old",
                "posted_at": old_iso,
                "enrichment": {},
            },
        ],
    }

    df = scrape_freehire(
        facets={"ai_archetype": ["agent_builder"], "exclude_blacklisted_ats": True},
        results_wanted=10,
        hours_old=24,
        processed_ids={"fh-already-processed-slug"},
        blacklisted_domains=["myworkdayjobs.com"],
        client=mock_client,
    )

    assert list(df.columns) == DF_COLS
    assert len(df) == 1
    row = df.iloc[0]
    assert row["id"] == "fh-senior-ai-engineer-acme-123"
    assert row["site"] == "freehire"
    assert row["job_url"] == "https://freehire.me/jobs/senior-ai-engineer-acme-123"
    assert row["job_url_direct"] == "https://boards.greenhouse.io/acme/jobs/123?utm_source=freehire.me"
    assert row["is_remote"] is True or bool(row["is_remote"]) is True
    assert row["job_level"] == "senior"
    assert row["job_type"] == "full_time"
    assert "140,000" in row["salary"]
    assert df.attrs["total_available"] == 3

    # Проверяем, что workday был передан в extra_source_exclude
    _, kwargs = mock_client.search_jobs.call_args
    assert kwargs["extra_source_exclude"] == ["workday"]


def test_freehire_router_endpoints():
    app = create_app()
    client = TestClient(app)

    r_def = client.get("/api/freehire/defaults")
    assert r_def.status_code == 200
    assert r_def.json()["defaults"]["work_mode"] == DEFAULT_FREEHIRE_FACETS["work_mode"]

    fake_facets_resp = {
        "total": 42,
        "facets": {
            "ai_archetype": {"agent_builder": 15, "rag_app_builder": 27},
            "skills": {"python": 30, "rag": 20, "agentic-ai": 12},
        },
    }
    with patch("job_filter.api.routers.freehire.FreeHireClient.get_facets", return_value=fake_facets_resp):
        r_fac = client.post("/api/freehire/facets", json={"facets": {"work_mode": ["remote"]}, "hours_old": 24})
        assert r_fac.status_code == 200
        body = r_fac.json()
        assert body["ok"] is True
        assert body["total"] == 42
        assert body["facets"]["ai_archetype"]["agent_builder"] == 15

        r_prof = client.get("/api/freehire/profile-skills")
        assert r_prof.status_code == 200
        assert r_prof.json()["ok"] is True
