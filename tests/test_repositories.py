"""Тесты репозиториев базы данных на чистой in-memory SQLite."""
import sqlite3
import pytest

from job_filter.db.schema import apply_schema, seed_initial_data
from job_filter.repositories import (
    blacklist_repo,
    candidate_repo,
    jobs_repo,
    skills_repo,
)


@pytest.fixture
def mem_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)
    seed_initial_data(conn)
    yield conn
    conn.close()


def test_seed_initial_data(mem_db):
    m = skills_repo.get_matrix(mem_db)
    assert len(m["categories"]) == 7
    assert len(m["skills"]) == 29

    boards = blacklist_repo.list_boards(mem_db)
    assert len(boards) >= 2


def test_candidate_settings_repo(mem_db):
    s = candidate_repo.get_settings(mem_db)
    assert s["profile_text"] == ""

    candidate_repo.save_settings(mem_db, profile_text="Test profile", cv_text="Test CV")
    s2 = candidate_repo.get_settings(mem_db)
    assert s2["profile_text"] == "Test profile"
    assert s2["cv_text"] == "Test CV"


def test_skills_repo_crud(mem_db):
    skills_repo.upsert_category(mem_db, "test_cat", "Test Category", 2.0, 20, 10)
    cat = skills_repo.get_category(mem_db, "test_cat")
    assert cat["title"] == "Test Category"

    skills_repo.upsert_skill(mem_db, "test_skill", "test_cat", "Test Skill", 3.0, 15, True, ["alias1"])
    m = skills_repo.get_matrix(mem_db)
    skill_ids = [s["skill_id"] for s in m["skills"]]
    assert "test_skill" in skill_ids

    skills_repo.delete_skill(mem_db, "test_skill")
    m2 = skills_repo.get_matrix(mem_db)
    assert "test_skill" not in [s["skill_id"] for s in m2["skills"]]

    skills_repo.delete_category_with_skills(mem_db, "test_cat")
    assert skills_repo.get_category(mem_db, "test_cat") is None


def test_jobs_repo_crud(mem_db):
    jobs_repo.replace_job(mem_db, {
        "job_id": "test-1",
        "title": "Engineer",
        "company": "Company",
        "url": "http://example.com",
        "date_posted": "2026-10-30",
        "matched": 1,
    })
    job = jobs_repo.get_job(mem_db, "test-1")
    assert job is not None
    assert job["title"] == "Engineer"

    jobs_repo.set_user_status(mem_db, "test-1", "applied")
    job = jobs_repo.get_job(mem_db, "test-1")
    assert job["user_status"] == "applied"

    jobs_repo.set_user_status(mem_db, "test-1", "rejected", user_reject_reason="Tech stack mismatch")
    job = jobs_repo.get_job(mem_db, "test-1")
    assert job["user_status"] == "rejected"
    assert job["user_reject_reason"] == "Tech stack mismatch"

    rejected_jobs = jobs_repo.get_user_rejected_jobs(mem_db)
    assert len(rejected_jobs) == 1
    assert rejected_jobs[0]["job_id"] == "test-1"
    assert rejected_jobs[0]["user_reject_reason"] == "Tech stack mismatch"

    jobs_repo.set_user_status(mem_db, "test-1", "new")
    job = jobs_repo.get_job(mem_db, "test-1")
    assert job["user_status"] == "new"
    assert job["user_reject_reason"] is None

