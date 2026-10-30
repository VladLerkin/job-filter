"""Тесты вычисления diff навыков между резюме и базой данных."""
from job_filter.models.cv import ParsedSkillItem
from job_filter.services.cv_service import compute_skills_diff


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
