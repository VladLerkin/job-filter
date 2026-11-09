"""Тесты адаптера Upwork (Apify Actors REST API)."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from job_filter.scraping.providers import SUPPORTED_SITES, scrape_site
from job_filter.scraping.upwork_adapter import (
    ApifyUpworkClient,
    _build_actor_input,
    _format_upwork_salary,
    _parse_upwork_date,
    normalize_actor_id,
    scrape_upwork,
)


def test_supported_sites_includes_upwork():
    assert "upwork" in SUPPORTED_SITES


def test_normalize_actor_id():
    assert normalize_actor_id("blackfalcondata/upwork-scraper") == "blackfalcondata~upwork-scraper"
    assert normalize_actor_id("fasty_dev~upwork-job-scraper") == "fasty_dev~upwork-job-scraper"
    assert normalize_actor_id("") == "blackfalcondata~upwork-scraper"


def test_build_actor_input_variants():
    p_neat = _build_actor_input("neatrat~upwork-job-scraper", "AI Agent", results_wanted=25, hours_old=12, payment_verified_only=True)
    assert p_neat["query"] == "AI Agent"
    assert p_neat["clientPaymentVerifiedOnly"] is True
    assert p_neat["maxJobAge"] == {"value": 12, "unit": "hours"}

    p_fasty = _build_actor_input("fasty_dev/upwork-job-scraper", "Python LangGraph", results_wanted=30)
    assert p_fasty["keywords"] == "Python LangGraph"
    assert p_fasty["limit"] == 30
    assert p_fasty["sortby"] == "newest"

    p_omkar = _build_actor_input("omkarcloud/upwork-jobs-scraper", "Kotlin Backend", results_wanted=20)
    assert p_omkar["query"] == "Kotlin Backend"
    assert p_omkar["pageStart"] == 1
    assert p_omkar["pageEnd"] == 2


def test_parse_upwork_date_relative_and_iso():
    ref = datetime(2026, 11, 9, 12, 0, 0, tzinfo=timezone.utc)
    dt_rel_min = _parse_upwork_date("15 minutes ago", now=ref)
    assert dt_rel_min == ref - timedelta(minutes=15)

    dt_rel_hr = _parse_upwork_date("3 hours ago", now=ref)
    assert dt_rel_hr == ref - timedelta(hours=3)

    dt_iso = _parse_upwork_date("2026-11-09T10:30:00Z", now=ref)
    assert dt_iso == datetime(2026, 11, 9, 10, 30, 0, tzinfo=timezone.utc)


def test_format_upwork_salary():
    assert _format_upwork_salary({"hourly_rate": {"min": 40, "max": 85}}) == "$40 - $85/hr (Hourly)"
    assert _format_upwork_salary({"rate": "$50.00 - $90.00"}) == "$50.00 - $90.00/hr (Hourly)"
    assert _format_upwork_salary({"budget": 3500}) == "$3,500 (Fixed-price)"
    assert _format_upwork_salary({}) is None


def test_scrape_upwork_unconfigured():
    client = ApifyUpworkClient(api_key="")
    df = scrape_upwork("Agentic Engineer", "Worldwide", results_wanted=5, client=client)
    assert df.empty
    assert "upwork" in df.attrs.get("errors", {})


def test_scrape_upwork_mocked_items():
    mock_client = MagicMock(spec=ApifyUpworkClient)
    mock_client.is_configured.return_value = True
    mock_client.actor_id = "neatrat~upwork-job-scraper"
    mock_client.run_actor_sync.return_value = [
        {
            "id": "~01abcdef1234567890",
            "title": "Senior Agentic AI Engineer (LangGraph & Python)",
            "jobUrl": "https://www.upwork.com/jobs/~01abcdef1234567890",
            "description": "We need an expert to build multi-agent workflows with LangGraph and Python.",
            "contractType": "Hourly",
            "rate": "$60.00 - $100.00",
            "experienceLevel": "Expert",
            "postedDate": "2 hours ago",
            "skills": ["Python", "LangGraph", "AI Agents"],
            "proposals": "5 to 10",
            "client": {
                "company_name": "Acme AI Labs",
                "paymentVerified": True,
                "location": {"country": "United States", "city": "Austin"},
                "stats": {"totalSpent": 45000, "rating": 4.98},
            },
        },
        {
            "ciphertext": "~02oldjob999999",
            "title": "Old Legacy Job",
            "description": "Python role",
            "postedDate": "5 days ago",
            "client": {"location": {"country": "Germany"}},
        },
    ]

    df = scrape_upwork(
        term="Agentic Engineer Remote",
        location="Worldwide",
        results_wanted=10,
        hours_old=24,
        client=mock_client,
        processed_ids=set(),
    )

    assert len(df) == 1
    row = df.iloc[0]
    assert row["id"] == "uw-01abcdef1234567890"
    assert row["site"] == "upwork"
    assert "Acme AI Labs" in row["company"]
    assert "United States" in row["company"]
    assert "$45k+ spent" in row["company"]
    assert row["salary"] == "$60.00 - $100.00/hr (Hourly)"
    assert row["is_remote"] == True  # noqa: E712
    assert "LangGraph" in row["description"]
    assert "Client Payment Verified: Yes" in row["description"]


def test_providers_scrape_site_dispatch_upwork(monkeypatch):
    monkeypatch.setattr("job_filter.config.APIFY_API_KEY", "")
    df = scrape_site(
        site="upwork",
        term="AI Agent Engineer",
        location="Worldwide",
        country_indeed="uk",
        results_wanted=5,
        hours_old=24,
        easy_apply=False,
    )
    assert df.empty
    assert "upwork" in df.attrs.get("errors", {})

