"""Тесты адаптера Hirify API (поиск, маппинг параметров, парсинг дат и зарплат)."""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest
import pandas as pd

from job_filter.scraping.hirify_adapter import (
    HirifyClient,
    _parse_published_date,
    _format_salary,
    scrape_hirify,
    scrape_hirify_feed,
    scrape_hirify_active_feeds,
)
from job_filter.scraping.providers import scrape_site, SUPPORTED_SITES


def test_supported_sites_includes_hirify():
    assert "hirify" in SUPPORTED_SITES


def test_client_is_configured():
    client_empty = HirifyClient(api_key="")
    assert not client_empty.is_configured()

    client_with_key = HirifyClient(api_key="test-key-123")
    assert client_with_key.is_configured()
    assert client_with_key.session.headers.get("Authorization") == "Bearer test-key-123"


def test_parse_published_date():
    dt1 = _parse_published_date("2026-10-30T14:20:00Z")
    assert dt1 is not None
    assert dt1.year == 2026
    assert dt1.month == 10
    assert dt1.day == 30

    dt2 = _parse_published_date("2026-10-31 10:00:00")
    assert dt2 is not None
    assert dt2.hour == 10

    dt3 = _parse_published_date("2026-10-29")
    assert dt3 is not None
    assert dt3.day == 29

    assert _parse_published_date(None) is None
    assert _parse_published_date("invalid-date") is None


def test_format_salary():
    assert _format_salary({"from": 4000, "to": 6000, "currency": "€", "period": "mo"}) == "€4,000 - €6,000/mo"
    assert _format_salary({"from": 5000, "currency": "$", "period": "mo"}) == "от $5,000/mo"
    assert _format_salary({"to": 8000, "currency": "$", "period": "mo"}) == "до $8,000/mo"
    assert _format_salary(None) is None
    assert _format_salary({}) is None


def test_scrape_hirify_unconfigured():
    client = HirifyClient(api_key="")
    df = scrape_hirify("Agentic Engineer", "Worldwide", results_wanted=5, client=client)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert "hirify" in df.attrs.get("errors", {})


def test_scrape_hirify_mocked_results():
    mock_client = MagicMock(spec=HirifyClient)
    mock_client.is_configured.return_value = True

    now_iso = datetime.now(timezone.utc).isoformat()
    old_iso = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()

    mock_client.search_vacancies.return_value = {
        "data": [
            {
                "vacancy_id": 101,
                "title": "Senior AI Agent Engineer",
                "slug": "senior-ai-agent-engineer-101",
                "company_masked": False,
                "company": "Acme AI Corp",
                "published_at": now_iso,
                "regions": ["Europe", "Worldwide"],
                "remote_type": "Remote",
                "grades": ["Senior"],
                "salary": {"from": 5000, "to": 7000, "currency": "$", "period": "mo"},
            },
            {
                "vacancy_id": 102,
                "title": "Old Vacancy",
                "slug": "old-vac-102",
                "published_at": old_iso,
                "salary": None,
            },
        ]
    }

    mock_client.read_vacancy.return_value = {
        "vacancy_id": 101,
        "description": "Full requirements: Python, LangGraph, LLM Agents.",
    }

    # hours_old=24: should include vacancy 101 and filter out vacancy 102
    df = scrape_hirify("AI Engineer", "Georgia", results_wanted=10, hours_old=24, client=mock_client)

    assert len(df) == 1
    row = df.iloc[0]
    assert row["id"] == "hf-101"
    assert row["site"] == "hirify"
    assert row["title"] == "Senior AI Agent Engineer"
    assert row["company"] == "Acme AI Corp"
    assert bool(row["is_remote"]) is True
    assert "LangGraph" in row["description"]
    assert row["salary"] == "$5,000 - $7,000/mo"


def test_providers_scrape_site_dispatch_hirify():
    # If unconfigured, calling scrape_site('hirify', ...) returns empty dataframe with error message
    df = scrape_site(
        site="hirify",
        term="Python",
        location="Worldwide",
        country_indeed="uk",
        results_wanted=5,
        hours_old=24,
        easy_apply=None,
    )
    assert isinstance(df, pd.DataFrame)


def test_scrape_hirify_feed_mocked():
    mock_client = MagicMock(spec=HirifyClient)
    mock_client.is_configured.return_value = True

    now_iso = datetime.now(timezone.utc).isoformat()
    mock_client.get_feed_vacancies.return_value = {
        "meta": {"feed": {"id": 60082, "name": "AI Agentic Engineer"}},
        "data": [
            {
                "vacancy_id": 201,
                "title": "Agentic AI Specialist",
                "slug": "agentic-ai-specialist-201",
                "company_masked": False,
                "company": "AgentLabs",
                "published_at": now_iso,
                "regions": ["Worldwide"],
                "remote_type": "global",
                "grades": ["Senior"],
                "salary": {"from": 6000, "to": 9000, "currency": "$", "period": "mo"},
            }
        ]
    }
    mock_client.read_vacancy.return_value = {
        "vacancy_id": 201,
        "description": "Agentic workflows with LangGraph and AutoGen",
    }

    df = scrape_hirify_feed(feed_id=60082, results_wanted=5, hours_old=24, client=mock_client)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["id"] == "hf-201"
    assert row["title"] == "Agentic AI Specialist"
    assert row["company"] == "AgentLabs"
    assert "LangGraph" in row["description"]


def test_scrape_hirify_active_feeds_mocked():
    mock_client = MagicMock(spec=HirifyClient)
    mock_client.is_configured.return_value = True

    mock_client.get_feeds.return_value = [
        {"id": 1, "name": "Feed Active", "is_active": True},
        {"id": 2, "name": "Feed Inactive", "is_active": False},
    ]

    now_iso = datetime.now(timezone.utc).isoformat()
    mock_client.get_feed_vacancies.return_value = {
        "data": [
            {
                "vacancy_id": 301,
                "title": "Staff Backend Engineer",
                "slug": "staff-backend-301",
                "company": "TechCorp",
                "published_at": now_iso,
            }
        ]
    }
    mock_client.read_vacancy.return_value = {"description": "Java and Spring Boot"}

    df = scrape_hirify_active_feeds(results_wanted=10, hours_old=24, client=mock_client)
    # Feed 2 is inactive, so only Feed 1 should be queried
    mock_client.get_feed_vacancies.assert_called_once_with(feed_id=1, page=1, per_page=20)
    assert len(df) == 1
    assert df.iloc[0]["id"] == "hf-301"


def test_providers_scrape_site_dispatch_hirify_feeds_mode():
    df = scrape_site(
        site="hirify",
        term="",
        location="",
        country_indeed="",
        results_wanted=5,
        hours_old=24,
        easy_apply=None,
        hirify_mode="feeds",
        hirify_feed_id="all_active",
    )
    assert isinstance(df, pd.DataFrame)
