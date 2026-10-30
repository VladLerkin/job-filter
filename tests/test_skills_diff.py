"""Тесты вычисления diff навыков между резюме и базой данных."""
import sqlite3
from job_filter.db.connection import connect, init_db
from job_filter.models.cv import ParsedSkillItem
from job_filter.repositories import skills_repo
from job_filter.services.cv_service import apply_cv_analysis, compute_skills_diff


def test_compute_skills_diff_categories():
    categories = [
        {"category_id": "ai_agentic", "title": "AI", "multiplier": 10.0, "max_points": 30},
        {"category_id": "core_backend", "title": "Backend", "multiplier": 2.0, "max_points": 20},
    ]
    existing_skills = [
        {"skill_id": "java", "name": "Java", "category_id": "core_backend", "years_experience": 8.0, "weight_points": 16},
        {"skill_id": "kotlin", "name": "Kotlin", "category_id": "core_backend", "years_experience": 5.0, "weight_points": 10},
    ]
    extracted = [
        ParsedSkillItem(skill_id="langgraph", name="LangGraph", category_id="ai_agentic", years_experience=2.0),
        ParsedSkillItem(skill_id="java", name="Java", category_id="core_backend", years_experience=10.0),
        ParsedSkillItem(skill_id="kotlin", name="Kotlin", category_id="core_backend", years_experience=5.0),
    ]

    diff = compute_skills_diff(extracted, existing_skills, categories)
    diff_by_id = {d["skill_id"]: d for d in diff}

    assert diff_by_id["langgraph"]["status"] == "new"
    assert diff_by_id["langgraph"]["new_points"] == 20
    assert diff_by_id["langgraph"]["selected"] is True

    assert diff_by_id["java"]["status"] == "updated"
    assert diff_by_id["java"]["old_years"] == 8.0
    assert diff_by_id["java"]["new_years"] == 10.0
    assert diff_by_id["java"]["new_points"] == 20
    assert diff_by_id["java"]["selected"] is True

    assert diff_by_id["kotlin"]["status"] == "unchanged"
    assert diff_by_id["kotlin"]["selected"] is False


def test_compute_skills_diff_with_missing_db_categories():
    # Only core_backend in DB categories
    categories = [
        {"category_id": "core_backend", "title": "Backend", "multiplier": 2.0, "max_points": 20},
    ]
    extracted = [
        ParsedSkillItem(skill_id="langgraph", name="LangGraph", category_id="ai_agentic", years_experience=2.0),
        ParsedSkillItem(skill_id="docker", name="Docker", category_id="arch_infra", years_experience=5.0),
    ]
    diff = compute_skills_diff(extracted, [], categories)
    diff_by_id = {d["skill_id"]: d for d in diff}

    # ai_agentic is from DEFAULT_SKILL_CATEGORIES: multiplier 15.0, max 30
    assert diff_by_id["langgraph"]["category_id"] == "ai_agentic"
    assert diff_by_id["langgraph"]["new_points"] == 30
    assert "AI & Agentic" in diff_by_id["langgraph"]["category_title"]

    # arch_infra is from DEFAULT_SKILL_CATEGORIES: multiplier 2.0, max 15
    assert diff_by_id["docker"]["category_id"] == "arch_infra"
    assert diff_by_id["docker"]["new_points"] == 10
    assert "Architecture" in diff_by_id["docker"]["category_title"]


def test_apply_cv_analysis_creates_default_category(tmp_path):
    db_file = tmp_path / "test.db"
    init_db(str(db_file))
    conn = connect(str(db_file))

    # Clean category table
    conn.execute("DELETE FROM skill_categories")
    conn.commit()

    skills_to_apply = [
        {
            "skill_id": "langgraph",
            "category_id": "ai_agentic",
            "name": "LangGraph",
            "years_experience": 2.0,
            "weight_points": 30,
            "is_primary": True,
            "aliases": ["langgraph", "langchain"],
        }
    ]

    applied, _ = apply_cv_analysis(
        conn,
        update_cv_text=False,
        structured_cv="",
        update_profile_text=False,
        candidate_summary="",
        apply_skills=True,
        skills_to_apply=skills_to_apply,
    )

    assert applied == 1
    cat = skills_repo.get_category(conn, "ai_agentic")
    assert cat is not None
    assert cat["multiplier"] == 15.0
    assert cat["max_points"] == 30
    assert "AI & Agentic" in cat["title"]

    skill = skills_repo.get_skill(conn, "langgraph")
    assert skill is not None
    assert skill["category_id"] == "ai_agentic"
    assert skill["weight_points"] == 30
    conn.close()

