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
    assert "profile_text" in res.json()


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


def test_blacklist_endpoints(client):
    res = client.get("/api/blacklist")
    assert res.status_code == 200
    assert "boards" in res.json()

    res_check = client.get("/api/blacklist/check?url=https://careers.icims.com/job&auto_link=false")
    assert res_check.status_code == 200
    assert res_check.json()["is_blacklisted"] is True


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

