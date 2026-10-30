"""Тесты утилит парсинга URL, доменов ATS и ключей компаний."""
from job_filter.utils.urls import (
    extract_host,
    extract_root_domain,
    find_domain_in_map,
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

