"""Тесты утилит парсинга URL, доменов ATS и ключей компаний."""
from job_filter.utils.urls import (
    extract_host,
    extract_root_domain,
    find_domain_in_map,
    is_search_aggregator_domain,
    is_utility_or_captcha_domain,
    normalize_company_key,
)


def test_extract_root_domain_ats():
    assert extract_root_domain("https://careers.icims.com/jobs/123") == "icims.com"
    assert extract_root_domain("sub.domain.cims.com") == "cims.com"
    assert extract_root_domain("company.myworkdayjobs.com/en-US/careers") == "myworkdayjobs.com"
    assert extract_root_domain("https://boards.greenhouse.io/corp") == "greenhouse.io"


def test_extract_root_domain_cctld():
    assert extract_root_domain("https://jobs.example.co.uk/role") == "example.co.uk"
    assert extract_root_domain("https://test.corp.com.au/apply") == "corp.com.au"
    assert extract_root_domain("https://www.google.com") == "google.com"


def test_extract_host():
    assert extract_host("https://www.example.com/path?q=1") == "example.com"
    assert extract_host("http://sub.domain.org:8080/") == "sub.domain.org"
    assert extract_host("just-a-domain.io") == "just-a-domain.io"
    assert extract_host("") == ""


def test_normalize_company_key():
    assert normalize_company_key("  Google   LLC  ") == "google llc"
    assert normalize_company_key(None) == ""


def test_find_domain_in_map():
    bad_map = {"icims.com": "Bad board", "cims.com": "Bad board"}
    assert find_domain_in_map("jobs.icims.com", bad_map) == "icims.com"
    assert find_domain_in_map("cims.com", bad_map) == "cims.com"
    assert find_domain_in_map("good-site.com", bad_map) is None


def test_is_utility_or_captcha_domain():
    assert is_utility_or_captcha_domain("https://newassets.hcaptcha.com/captcha/v1/something") is True
    assert is_utility_or_captcha_domain("hcaptcha.com") is True
    assert is_utility_or_captcha_domain("https://www.google.com/recaptcha/api.js") is True
    assert is_utility_or_captcha_domain("challenges.cloudflare.com") is True
    assert is_utility_or_captcha_domain("https://jobs.lever.co/corp") is False
    assert is_utility_or_captcha_domain("greenhouse.io") is False
    assert is_utility_or_captcha_domain(None) is False


def test_is_search_aggregator_domain():
    assert is_search_aggregator_domain("https://www.linkedin.com/jobs/view/12345") is True
    assert is_search_aggregator_domain("linkedin.com") is True
    assert is_search_aggregator_domain("https://hirify.me/jobs/1364896") is True
    assert is_search_aggregator_domain("hirify.me") is True
    assert is_search_aggregator_domain("https://www.indeed.com/viewjob?jk=123") is True
    assert is_search_aggregator_domain("indeed.com") is True
    assert is_search_aggregator_domain("de.indeed.com") is True
    assert is_search_aggregator_domain("indeed.co.uk") is True
    assert is_search_aggregator_domain("https://www.glassdoor.com/job-listing/123") is True
    assert is_search_aggregator_domain("glassdoor.com") is True
    assert is_search_aggregator_domain("glassdoor.co.uk") is True
    assert is_search_aggregator_domain("jobs.lever.co") is False
    assert is_search_aggregator_domain("boards.greenhouse.io") is False
    assert is_search_aggregator_domain("cims.com") is False
    assert is_search_aggregator_domain(None) is False


def test_scrape_linkedin_search_retries_on_429_and_dns(monkeypatch):
    import requests
    from job_filter.scraping.linkedin import scrape_linkedin_search

    html_page = """
    <div class="base-search-card" data-entity-urn="urn:li:jobPosting:999001">
      <h3 class="base-search-card__title">Senior AI Agent Engineer (Remote)</h3>
      <h4 class="base-search-card__subtitle"><a href="https://linkedin.com/company/acme">Acme AI</a></h4>
      <span class="job-search-card__location">EMEA</span>
      <time datetime="2026-11-08">Today</time>
    </div>
    """

    calls = {"count": 0}

    class DummyResp:
        def __init__(self, status_code: int, text: str = "", headers: dict | None = None):
            self.status_code = status_code
            self.text = text
            self.headers = headers or {}

    def fake_get(self, url, params=None, headers=None, timeout=15):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.ConnectionError("NameResolutionError: Failed to resolve www.linkedin.com")
        if calls["count"] == 2:
            return DummyResp(429, headers={"Retry-After": "0"})
        return DummyResp(200, text=html_page)

    monkeypatch.setattr(requests.Session, "get", fake_get)
    monkeypatch.setattr("job_filter.scraping.linkedin.time.sleep", lambda _: None)

    df = scrape_linkedin_search("Agentic Engineer Remote", "EMEA", results_wanted=10, page_delay_range=(0, 0))
    assert len(df) == 1
    assert df.iloc[0]["id"] == "li-999001"
    assert bool(df.iloc[0]["is_remote"]) is True
    assert df.attrs.get("had_rate_limit") is True
    assert not df.attrs.get("errors")

