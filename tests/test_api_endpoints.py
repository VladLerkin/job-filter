"""Интеграционные тесты API через FastAPI TestClient."""
import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Job Filter" in res.text


def test_static_files(client):
    res_css = client.get("/static/css/style.css")
    assert res_css.status_code == 200
    assert ".badge-top" in res_css.text

    res_js = client.get("/static/js/app.js")
    assert res_js.status_code == 200
    assert "loadSkillsMatrix" in res_js.text


def test_candidate_endpoints(client):
    res = client.get("/api/candidate")
    assert res.status_code == 200
    data = res.json()
    assert "profile_text" in data
    assert "geo_preferences" in data
    assert "current_location" in data["geo_preferences"]

    put_res = client.put(
        "/api/candidate",
        json={
            "profile_text": data["profile_text"],
            "cv_text": data["cv_text"],
            "geo_preferences": {
                **data["geo_preferences"],
                "relocation_policy": "with_sponsorship_only",
            },
        },
    )
    assert put_res.status_code == 200
    assert put_res.json()["geo_preferences"]["relocation_policy"] == "with_sponsorship_only"


def test_skills_matrix_endpoint(client):
    res = client.get("/api/skills/matrix")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "skills" in data


def test_jobs_list_endpoint(client):
    res = client.get("/api/jobs?tab=actionable")
    assert res.status_code == 200
    data = res.json()
    assert "stats" in data
    assert "jobs" in data


def test_job_rejection_status_and_learning_data(client):
    from job_filter.db.connection import connect
    from job_filter.repositories import jobs_repo

    test_id = "test-reject-endpoint-1"
    conn = connect()
    try:
        jobs_repo.replace_job(conn, {
            "job_id": test_id,
            "title": "Backend Dev",
            "company": "RejectTest Corp",
            "url": "http://example.com/reject",
            "date_posted": "2026-11-05",
            "matched": 1,
            "score": 80,
        })
        conn.commit()
    finally:
        conn.close()

    # Mark as rejected with reason
    patch_res = client.patch(
        f"/api/jobs/{test_id}/status",
        json={
            "user_status": "rejected",
            "user_reject_reason": "Not enough remote flexibility (requires on-site visits)",
        },
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["user_status"] == "rejected"
    assert "remote flexibility" in patch_res.json()["user_reject_reason"]

    # Verify tab=actionable excludes it
    act_res = client.get("/api/jobs?tab=actionable")
    assert act_res.status_code == 200
    act_ids = [j["job_id"] for j in act_res.json()["jobs"]]
    assert test_id not in act_ids

    # Verify tab=rejected includes it
    rej_res = client.get("/api/jobs?tab=rejected")
    assert rej_res.status_code == 200
    rej_job = next((j for j in rej_res.json()["jobs"] if j["job_id"] == test_id), None)
    assert rej_job is not None
    assert rej_job["user_reject_reason"] == "Not enough remote flexibility (requires on-site visits)"

    # Verify training data endpoint
    learn_res = client.get("/api/jobs/user-rejections")
    assert learn_res.status_code == 200
    rejections = learn_res.json()
    found = next((r for r in rejections if r["job_id"] == test_id), None)
    assert found is not None
    assert found["user_reject_reason"] == "Not enough remote flexibility (requires on-site visits)"

    # Return to new
    reset_res = client.patch(
        f"/api/jobs/{test_id}/status",
        json={"user_status": "new"},
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["user_status"] == "new"

    # Cleanup test record
    conn = connect()
    try:
        conn.execute("DELETE FROM processed_jobs WHERE job_id = ?", (test_id,))
        conn.commit()
    finally:
        conn.close()


def test_blacklist_endpoints(client):
    res = client.get("/api/blacklist")
    assert res.status_code == 200
    assert "boards" in res.json()

    res_check = client.get("/api/blacklist/check?url=https://careers.icims.com/job&auto_link=false")
    assert res_check.status_code == 200
    assert res_check.json()["is_blacklisted"] is True

    # Aggregators cannot be blacklisted
    bad_res = client.post(
        "/api/blacklist",
        json={"domain_or_url": "https://www.linkedin.com/jobs/view/123", "reason": "test"},
    )
    assert bad_res.status_code == 400
    assert "агрегатор" in bad_res.json()["detail"]


def test_pipeline_status(client):
    res = client.get("/api/pipeline/status")
    assert res.status_code == 200
    assert "running" in res.json()


def test_hirify_feeds_endpoint(client):
    res = client.get("/api/hirify/feeds")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "feeds" in data

