"""Тесты многоуровневой детерминированной дедупликации вакансий."""
import sqlite3
import pytest

from job_filter.db.schema import apply_schema
from job_filter.repositories import jobs_repo
from job_filter.utils.dedup import (
    DeduplicationIndex,
    is_generic_company,
    normalize_apply_url,
    normalize_company,
    normalize_title,
    normalized_title_company_key,
)


def test_normalize_company_strips_suffixes_and_symbols():
    assert normalize_company("Sprout Social, Inc.") == "sprout social"
    assert normalize_company("Akamai Technologies") == "akamai"
    assert normalize_company("Oyster®") == "oyster"
    assert normalize_company("QEMETICA Global Solutions Sp. z o.o.") == "qemetica global solutions"
    assert normalize_company("Acme Corp.") == "acme"
    assert normalize_company("Acme, LLC") == "acme"


def test_is_generic_company():
    assert is_generic_company(normalize_company("Hirify Employer")) is True
    assert is_generic_company(normalize_company("Confidential")) is True
    assert is_generic_company(normalize_company("Upwork Client (United States)")) is True
    assert is_generic_company(normalize_company("")) is True
    assert is_generic_company(normalize_company("Distru")) is False


def test_normalize_title_handles_punctuation_abbrevs_and_noise():
    assert normalize_title("Principal Engineer- Agentic Development") == normalize_title(
        "Principal Engineer - Agentic Development"
    )
    assert normalize_title("Sr. Staff AI Engineer (Remote Eligible)") == normalize_title(
        "Senior Staff AI Engineer (Remote Eligible)"
    )
    assert normalize_title("Agentic AI Engineer - Remote Work | REF#304845") == normalize_title(
        "Agentic AI Engineer - Remote Work"
    )
    assert normalize_title("Senior LLM Engineer (Remote, Durban)") == normalize_title(
        "Senior LLM Engineer (Remote, Bogota)"
    )
    assert normalize_title("Java Developer - CC Digital (f/m/x)") == normalize_title(
        "Java Developer - CC Digital"
    )
    assert normalize_title("Full-Stack Engineer") == normalize_title("Fullstack Engineer")


def test_normalized_title_company_key_ignores_generic_companies():
    assert normalized_title_company_key("Senior Python Developer", "Hirify Employer") == ""
    assert normalized_title_company_key("Senior Python Developer", "Confidential") == ""
    assert (
        normalized_title_company_key("Senior Software Engineer", "Akamai Technologies")
        == normalized_title_company_key("Senior Software Engineer", "Akamai")
    )


def test_normalize_apply_url():
    u1 = normalize_apply_url(
        "https://jobs.lever.co/distru/42737937-162f-4933-a80a-a7eee9f44cb1/apply?source=LinkedIn&utm_medium=social"
    )
    u2 = normalize_apply_url(
        "https://www.jobs.lever.co/distru/42737937-162f-4933-a80a-a7eee9f44cb1/apply/"
    )
    assert u1 == u2
    assert u1 != ""

    # Значимые параметры (gh_jid) сохраняются
    g1 = normalize_apply_url("https://boards.greenhouse.io/company/jobs?gh_jid=111&gh_src=abc")
    g2 = normalize_apply_url("https://boards.greenhouse.io/company/jobs?gh_jid=222&gh_src=xyz")
    assert g1 != g2

    # Пустой корень домена не используется для дедупликации
    assert normalize_apply_url("https://company.com/") == ""
    assert normalize_apply_url("not-a-url") == ""


def test_cross_board_hirify_linkedin_dedup():
    idx = DeduplicationIndex()
    idx.add(
        job_id="hf-1387293",
        title="Staff AI Product Engineer (Agentic AI)",
        company="Distru",
        apply_url="https://jobs.lever.co/distru/42737937-162f-4933-a80a-a7eee9f44cb1/apply?source=LinkedIn",
    )
    idx.add(
        job_id="li-4485830569",
        title="Staff Platform Engineer, Agentic Engineering",
        company="n8n",
    )
    idx.add(
        job_id="hf-1323647",
        title="Principal Engineer - Agentic Development (AI)",
        company="FICO",
    )

    # Distru: совпадает по apply_url и по fuzzy_title
    assert idx.find_pre_fetch_duplicate(
        "Staff AI Product Engineer | REMOTE",
        "Distru",
        apply_url="https://jobs.lever.co/distru/42737937-162f-4933-a80a-a7eee9f44cb1/apply",
    ) == ("hf-1387293", "apply_url")
    assert idx.find_pre_fetch_duplicate(
        "Staff AI Product Engineer | REMOTE",
        "Distru",
    ) == ("hf-1387293", "fuzzy_title")

    # n8n: LinkedIn -> Hirify
    assert idx.find_pre_fetch_duplicate(
        "Staff Platform Engineer (AI Agentic Engineering)",
        "n8n",
    ) == ("li-4485830569", "fuzzy_title")

    # FICO: Hirify -> LinkedIn с кривым дефисом
    assert idx.find_pre_fetch_duplicate(
        "Principal Engineer- Agentic Development",
        "FICO",
    ) == ("hf-1323647", "fuzzy_title")


def test_fuzzy_title_does_not_merge_distinct_roles_or_seniorities():
    idx = DeduplicationIndex()
    idx.add(job_id="j-1", title="Software Engineer (Java)", company="Acme")
    idx.add(job_id="j-2", title="Senior Backend Engineer", company="Beta")
    idx.add(job_id="j-3", title="Staff Software Developer, AI Innovation", company="Kinaxis")
    idx.add(job_id="j-4", title="Forward Deployed Engineer (AI)", company="Camunda")

    assert idx.find_pre_fetch_duplicate("Software Engineer (Python)", "Acme") is None
    assert idx.find_pre_fetch_duplicate("Senior Frontend Engineer", "Beta") is None
    assert idx.find_pre_fetch_duplicate("Software Developer, AI Innovation", "Kinaxis") is None
    assert idx.find_pre_fetch_duplicate("Senior Forward Deployed Engineer (AI)", "Camunda") is None


def test_post_fetch_description_dedup_catches_proxy_aggregators():
    desc = (
        "We are looking for a Forward Deployed Engineer to join our Agentic Platform team "
        "working closely with UK Public Sector customers. You will build production AI agents, "
        "integrate enterprise APIs, design evaluation pipelines, and deliver secure scalable "
        "cloud systems using Python, TypeScript, Docker, and Kubernetes in fast iterative cycles."
    )
    idx = DeduplicationIndex()
    idx.add(
        job_id="li-4456846503",
        title="Forward Deployed Engineer, Agentic Platform (UK Public Sector)",
        company="Cohere",
        description=desc,
    )

    # Прокси-компания с другим названием, но тем же описанием
    assert idx.find_pre_fetch_duplicate(
        "Forward Deployed Engineer, Agentic Platform (UK Public Sector)",
        "Deployed Lab",
    ) is None
    assert idx.find_post_fetch_duplicate(description=desc) == ("li-4456846503", "description")

    # Совершенно другое описание не должно совпадать
    other_desc = (
        "Join our mobile payments squad to develop native iOS applications in Swift and SwiftUI. "
        "You will collaborate with product designers, maintain CoreData storage layers, optimize "
        "animations, and publish weekly App Store releases with automated UI tests."
    )
    assert idx.find_post_fetch_duplicate(description=other_desc) is None


def test_list_dedup_records_excludes_duplicate_stubs():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)

    jobs_repo.replace_job(conn, {
        "job_id": "orig-1",
        "title": "Senior Engineer",
        "company": "Acme",
        "url": "https://example.com/1",
        "date_posted": "2026-11-19",
        "matched": 1,
        "reject_reason": None,
    })
    jobs_repo.replace_job(conn, {
        "job_id": "dup-2",
        "title": "Senior Engineer",
        "company": "Acme",
        "url": "https://example.com/2",
        "date_posted": "2026-11-19",
        "matched": 0,
        "reject_reason": "duplicate_of:orig-1",
    })
    conn.commit()

    recs = jobs_repo.list_dedup_records(conn)
    assert [r["job_id"] for r in recs] == ["orig-1"]
    conn.close()


def test_original_title_bidirectional_cross_board_dedup():
    # 1. LinkedIn сохранён первым, затем приходит Hirify с переименованным title и точным original_title
    idx1 = DeduplicationIndex()
    idx1.add(
        job_id="li-9001",
        title="Software Engineer, Core Platform",
        company="Intetics",
    )
    assert idx1.find_pre_fetch_duplicate(
        title="Senior Backend Developer (Java / AI)",
        original_title="Software Engineer, Core Platform",
        company="Intetics",
    ) == ("li-9001", "original_title")

    # 2. Hirify сохранён первым (с original_title), затем приходит LinkedIn с оригинальным заголовком
    idx2 = DeduplicationIndex()
    idx2.add(
        job_id="hf-1429943",
        title="Senior Agentic QA Engineer (AI)",
        original_title="Senior Agentic QA Engineer",
        company="Intetics",
    )
    assert idx2.find_pre_fetch_duplicate(
        title="Senior Agentic QA Engineer",
        company="Intetics",
    ) == ("hf-1429943", "norm_title_company")

