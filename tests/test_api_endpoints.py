"""Интеграционные тесты API через FastAPI TestClient на изолированной тестовой БД."""
import pytest
from fastapi.testclient import TestClient

from app import app
from job_filter import config
from job_filter.db.connection import init_db
from job_filter.scoring.matrix import invalidate_matrix_cache


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_api_jobs.db"
    monkeypatch.setattr(config, "DB_PATH", test_db)
    invalidate_matrix_cache()
    init_db(test_db)
    yield test_db
    invalidate_matrix_cache()


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
            "profile_text": "Updated profile text",
            "cv_text": "Updated CV markdown",
            "geo_preferences": {
                **data["geo_preferences"],
                "relocation_policy": "no_relocation",
            },
        },
    )
    assert put_res.status_code == 200
    assert put_res.json()["geo_preferences"]["relocation_policy"] == "no_relocation"

    # Проверяем, что изменения реально закоммитились в SQLite после закрытия соединения
    get_after = client.get("/api/candidate")
    assert get_after.status_code == 200
    after_data = get_after.json()
    assert after_data["profile_text"] == "Updated profile text"
    assert after_data["cv_text"] == "Updated CV markdown"
    assert after_data["geo_preferences"]["relocation_policy"] == "no_relocation"


def test_skills_matrix_endpoint(client):
    res = client.get("/api/skills/matrix")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "skills" in data


def test_jobs_list_granular_tabs(client):
    from job_filter.db.connection import connect
    from job_filter.repositories import jobs_repo

    conn = connect()
    try:
        jobs_repo.replace_job(conn, {
            "job_id": "test-top-job",
            "title": "Top Match Role",
            "company": "TopCo",
            "url": "http://example.com/top",
            "matched": 1,
            "score": 75,
        })
        jobs_repo.replace_job(conn, {
            "job_id": "test-good-job",
            "title": "Good Match Role",
            "company": "GoodCo",
            "url": "http://example.com/good",
            "matched": 1,
            "score": 65,
        })
        jobs_repo.replace_job(conn, {
            "job_id": "test-fair-job",
            "title": "Fair Match Role",
            "company": "FairCo",
            "url": "http://example.com/fair",
            "matched": 1,
            "score": 55,
        })
        conn.commit()

        res_top = client.get("/api/jobs?tab=top")
        assert res_top.status_code == 200
        top_ids = [j["job_id"] for j in res_top.json()["jobs"]]
        assert "test-top-job" in top_ids
        assert "test-good-job" not in top_ids
        assert "test-fair-job" not in top_ids

        res_good = client.get("/api/jobs?tab=good")
        assert res_good.status_code == 200
        good_ids = [j["job_id"] for j in res_good.json()["jobs"]]
        assert "test-good-job" in good_ids
        assert "test-top-job" not in good_ids
        assert "test-fair-job" not in good_ids

        res_fair = client.get("/api/jobs?tab=fair")
        assert res_fair.status_code == 200
        fair_ids = [j["job_id"] for j in res_fair.json()["jobs"]]
        assert "test-fair-job" in fair_ids
        assert "test-top-job" not in fair_ids
        assert "test-good-job" not in fair_ids

        stats = res_top.json()["stats"]
        assert "fair_match" in stats
        assert "good_match" in stats
        assert "top_match" in stats
    finally:
        conn.execute("DELETE FROM processed_jobs WHERE job_id IN (?, ?, ?)", ("test-top-job", "test-good-job", "test-fair-job"))
        conn.commit()
        conn.close()


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


def test_rejected_tab_subcategories_and_restoring(client):
    from job_filter.db.connection import connect
    from job_filter.repositories import jobs_repo

    user_job_id = "test-user-rej-1"
    auto_job_id = "test-auto-rej-1"
    conn = connect()
    try:
        # 1. Job rejected by user
        jobs_repo.replace_job(conn, {
            "job_id": user_job_id,
            "title": "Agentic Engineer",
            "company": "UserRej Corp",
            "url": "http://example.com/user-rej",
            "date_posted": "2026-11-06",
            "matched": 1,
            "score": 75,
            "user_status": "rejected",
            "user_reject_reason": "Командировки",
        })
        # 2. Job rejected automatically
        jobs_repo.replace_job(conn, {
            "job_id": auto_job_id,
            "title": "Junior Python Dev",
            "company": "AutoRej Corp",
            "url": "http://example.com/auto-rej",
            "date_posted": "2026-11-06",
            "matched": 0,
            "score": 30,
            "reject_reason": "single_country_lock:UK-only",
            "user_status": "new",
        })
        conn.commit()
    finally:
        conn.close()

    try:
        # Check tab=rejected
        rej_res = client.get("/api/jobs?tab=rejected")
        assert rej_res.status_code == 200
        data = rej_res.json()
        assert "rejected_user" in data["stats"]
        assert "rejected_auto" in data["stats"]

        u_job = next((j for j in data["jobs"] if j["job_id"] == user_job_id), None)
        assert u_job is not None
        assert u_job["rejection_source"] == "user"
        assert u_job["rejection_category"] == "user_manual"
        assert u_job["rejection_reason_display"] == "Командировки"

        a_job = next((j for j in data["jobs"] if j["job_id"] == auto_job_id), None)
        assert a_job is not None
        assert a_job["rejection_source"] == "auto"
        assert a_job["rejection_category"] == "location"
        assert "UK-only" in a_job["rejection_reason_display"]

        # Restore auto job to feed via saved status
        patch_res = client.patch(
            f"/api/jobs/{auto_job_id}/status",
            json={"user_status": "saved"},
        )
        assert patch_res.status_code == 200

        # Check that saved job now appears in actionable
        act_res = client.get("/api/jobs?tab=actionable")
        assert act_res.status_code == 200
        saved_job = next((j for j in act_res.json()["jobs"] if j["job_id"] == auto_job_id), None)
        assert saved_job is not None
        assert saved_job["user_status"] == "saved"

        # And is excluded from tab=rejected
        rej_res2 = client.get("/api/jobs?tab=rejected")
        assert rej_res2.status_code == 200
        assert not any(j["job_id"] == auto_job_id for j in rej_res2.json()["jobs"])
    finally:
        conn = connect()
        try:
            conn.execute("DELETE FROM processed_jobs WHERE job_id IN (?, ?)", (user_job_id, auto_job_id))
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


def test_job_description_and_rescore_diff_endpoints(client):
    from job_filter.db.connection import connect
    from job_filter.repositories import jobs_repo

    conn = connect()
    try:
        jobs_repo.replace_job(conn, {
            "job_id": "test-desc-1",
            "title": "Senior AI Engineer",
            "company": "AgentCo",
            "url": "http://example.com/desc",
            "description": "Full vacancy markdown description here",
            "matched": 0,
            "score": 40,
            "reject_reason": "country_pool_lock:Czechia, Slovakia",
        })
        conn.commit()
    finally:
        conn.close()

    desc_res = client.get("/api/jobs/test-desc-1/description")
    assert desc_res.status_code == 200
    assert desc_res.json()["description"] == "Full vacancy markdown description here"

    rej_res = client.get("/api/jobs?tab=rejected")
    assert rej_res.status_code == 200
    job = next((j for j in rej_res.json()["jobs"] if j["job_id"] == "test-desc-1"), None)
    assert job is not None
    assert job["has_description"] is True
    assert job["rejection_category"] == "location"
    assert "Czechia, Slovakia" in job["rejection_reason_display"]

    diff_res = client.get("/api/jobs/rescore-diff")
    assert diff_res.status_code == 200
    assert "promoted_to_matched" in diff_res.json()


def test_applied_tracker_sync_and_stages(client, monkeypatch):
    import json
    from job_filter.db.connection import connect
    from job_filter.llm import application_tracker
    from job_filter.repositories import jobs_repo

    conn = connect()
    try:
        for jid, comp, title in [
            ("app-1", "Teradata", "Staff AI Engineer"),
            ("app-2", "ITHAKA", "Principal Software Engineer (Backend)"),
            ("app-3", "Glia", "Senior Software Engineer - Conversational AI"),
            ("app-4", "SilentCorp", "Backend Kotlin Developer"),
        ]:
            jobs_repo.replace_job(conn, {
                "job_id": jid,
                "title": title,
                "company": comp,
                "url": f"http://example.com/{jid}",
                "matched": 1,
                "score": 80,
                "user_status": "applied",
            })
        conn.commit()
    finally:
        conn.close()

    # 1. Check prompt generation for @job-application-tracker
    prompt_res = client.get("/api/jobs/applied-tracker/prompt")
    assert prompt_res.status_code == 200
    prompt_data = prompt_res.json()
    assert prompt_data["applied_count"] == 4
    assert "@job-application-tracker" in prompt_data["prompt"]
    assert "Teradata" in prompt_data["prompt"]
    assert "ITHAKA" in prompt_data["prompt"]
    assert "Glia" in prompt_data["prompt"]

    # 2. Test sync with mocked LLM response
    fake_llm_json = json.dumps({
        "summary": "1 подтверждение, 1 отказ, 1 приглашение на интервью",
        "updates": [
            {"company": "Teradata", "stage": "confirmed", "reason": "Подтверждение получено"},
            {"company": "ITHAKA", "stage": "rejected_by_company", "reason": "Выбрали кандидатов с опытом в США"},
            {"company": "Glia", "stage": "interview", "reason": "Приглашение на HR-скрининг 30 мин"},
        ],
    })
    monkeypatch.setattr(application_tracker, "run_agy", lambda *a, **kw: fake_llm_json)

    sync_res = client.post(
        "/api/jobs/applied-tracker/sync",
        json={"report_text": "Teradata confirmed, ITHAKA rejected, Glia invited to HR screening"},
    )
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["updated_count"] == 3
    assert sync_data["stage_counts"]["confirmed"] == 1
    assert sync_data["stage_counts"]["rejected_by_company"] == 1
    assert sync_data["stage_counts"]["interview"] == 1

    # 3. Check tab=applied stats and ordering (interview first!)
    app_res = client.get("/api/jobs?tab=applied")
    assert app_res.status_code == 200
    app_data = app_res.json()
    stats = app_data["stats"]
    assert stats["applied"] == 4
    assert stats["applied_waiting"] == 1
    assert stats["applied_confirmed"] == 1
    assert stats["applied_interview"] == 1
    assert stats["applied_rejected"] == 1

    jobs = app_data["jobs"]
    assert jobs[0]["job_id"] == "app-3"
    assert jobs[0]["application_stage"] == "interview"
    assert jobs[0]["application_email_url"] is not None
    assert "mail.google.com/mail/u/0/#search/" in jobs[0]["application_email_url"]
    ithaka = next(j for j in jobs if j["job_id"] == "app-2")
    assert ithaka["application_stage"] == "rejected_by_company"
    assert ithaka["company_reject_reason"] == "Выбрали кандидатов с опытом в США"

    # 4. Verify next prompt excludes already-rejected company (ITHAKA) from active check list
    prompt_res2 = client.get("/api/jobs/applied-tracker/prompt")
    assert prompt_res2.status_code == 200
    next_prompt = prompt_res2.json()["prompt"]
    assert "Principal Software Engineer (Backend)" not in next_prompt
    assert "Не включай в отчёт компании, по которым отказ уже занесён в базу: ITHAKA" in next_prompt

    # 5. Test manual PATCH /api/jobs/{job_id}/application-stage
    stage_res = client.patch(
        "/api/jobs/app-4/application-stage",
        json={
            "application_stage": "confirmed",
            "company_reject_reason": "Auto-acknowledgement email",
        },
    )
    assert stage_res.status_code == 200
    assert stage_res.json()["application_stage"] == "confirmed"


def test_macro_settings_and_provider_checks_and_cross_board_dedup(client, monkeypatch):
    from job_filter.db.connection import connect
    from job_filter.repositories import jobs_repo
    from job_filter.services import pipeline

    # 1. Check initial macro settings & provider check statuses
    res_get = client.get("/api/pipeline/macro-settings")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert "macro_settings" in data_get
    assert "provider_checks" in data_get
    assert data_get["macro_settings"]["execution_mode"] == "per_provider"
    assert data_get["macro_settings"]["hours_mode"] == "auto_from_last_run"
    assert set(data_get["provider_checks"].keys()) == {"linkedin", "indeed", "glassdoor", "hirify"}

    # 2. Save updated macro settings
    new_settings = {
        "execution_mode": "batch_all_then_llm",
        "hours_mode": "fixed",
        "default_hours_old": 12,
        "max_auto_hours_old": 48,
        "results_wanted": 30,
        "llm_limit": 25,
        "steps": [
            {
                "site": "hirify",
                "enabled": True,
                "hirify_mode": "feeds",
                "hirify_feed_id": "all_active",
                "locations": ["Worldwide"],
                "countries": [],
            },
            {
                "site": "linkedin",
                "enabled": True,
                "locations": ["EMEA"],
                "countries": [],
                "easy_apply": False,
            },
            {
                "site": "indeed",
                "enabled": True,
                "locations": [],
                "countries": ["uk", "unitedarabemirates", "czechrepublic"],
                "easy_apply": False,
            },
        ],
    }
    res_put = client.put("/api/pipeline/macro-settings", json=new_settings)
    assert res_put.status_code == 200
    saved = res_put.json()["macro_settings"]
    assert saved["execution_mode"] == "batch_all_then_llm"
    assert saved["hours_mode"] == "fixed"
    assert saved["default_hours_old"] == 12
    assert len(saved["steps"]) == 4
    assert len([s for s in saved["steps"] if s["enabled"]]) == 3

    # 3. Record provider check and verify status endpoint reflects it
    conn = connect()
    try:
        pipeline.record_provider_check(
            conn,
            "linkedin",
            hours_old_used=6,
            fetched_count=42,
            matched_count=7,
            location="EMEA",
        )
        jobs_repo.replace_job(conn, {
            "job_id": "existing-li-1",
            "title": "Senior Agentic AI Engineer",
            "company": "Acme Robotics",
            "site": "linkedin",
            "url": "https://linkedin.com/jobs/view/1",
            "matched": 1,
            "score": 85,
        })
        conn.commit()
        keys = jobs_repo.get_processed_title_company_keys(conn)
        assert "senior agentic ai engineer::acme robotics" in keys
    finally:
        conn.close()

    res_status = client.get("/api/pipeline/providers-status")
    assert res_status.status_code == 200
    li_check = res_status.json()["provider_checks"]["linkedin"]
    assert li_check["last_checked_at"] is not None
    assert li_check["fetched_count"] == 42
    assert li_check["matched_count"] == 7
    assert li_check["recommended_hours_old"] >= 2

    # 4. Verify run_macro_pipeline executes steps in both modes
    calls = []

    def fake_fetch_and_filter_jobs(**kwargs):
        calls.append(("fetch", kwargs["site_names"][0], kwargs.get("location"), kwargs.get("run_llm_enrichment")))
        return []

    def fake_enrich(conn, **kwargs):
        calls.append(("enrich", kwargs.get("limit")))
        return 3

    monkeypatch.setattr(pipeline, "fetch_and_filter_jobs", fake_fetch_and_filter_jobs)
    monkeypatch.setattr(pipeline, "enrich_and_score_pending_jobs", fake_enrich)

    summary_batch = pipeline.run_macro_pipeline()
    assert summary_batch["execution_mode"] == "batch_all_then_llm"
    assert summary_batch["steps_executed"] == 3
    assert ("fetch", "hirify", "Worldwide", False) in calls
    assert ("fetch", "linkedin", "EMEA", False) in calls
    assert ("fetch", "indeed", "uk", False) in calls
    assert ("fetch", "indeed", "united arab emirates", False) in calls
    assert ("fetch", "indeed", "czech republic", False) in calls
    assert ("enrich", 25) in calls



