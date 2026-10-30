"""Тесты извлечения JSON из вывода моделей и валидации моделей."""
import pytest

from job_filter.llm.agy_client import extract_json_object, unwrap_structured_output
from job_filter.models.cv import ParsedCVResult, ParsedSkillItem
from job_filter.models.enrichment import JobEnrichment


def test_extract_json_from_plain():
    text = '{"name": "test", "val": 123}'
    res = extract_json_object(text)
    assert res == {"name": "test", "val": 123}


def test_extract_json_from_markdown():
    text = """Here is the result:
```json
{
  "key": "value",
  "nested": {"inner": 1}
}
```
Done!"""
    res = extract_json_object(text)
    assert res == {"key": "value", "nested": {"inner": 1}}


def test_extract_json_multiline_with_inner_single_line_objects():
    # Проверка, что парсер не срезается на внутреннюю строку с {...}
    text = """
    ```json
    {
      "candidate_summary": "Lead Eng",
      "skills": [
        {"skill_id": "java", "name": "Java"}
      ]
    }
    ```
    """
    res = extract_json_object(text)
    assert "candidate_summary" in res
    assert len(res["skills"]) == 1
    assert res["skills"][0]["skill_id"] == "java"


def test_parsed_skill_item_normalization():
    item = ParsedSkillItem.model_validate({
        "skill_id": "python",
        "category": "secondary_backend",  # алиас category -> category_id
        "years_experience": "5+ years",   # парсинг строки
    })
    assert item.skill_id == "python"
    assert item.category_id == "secondary_backend"
    assert item.years_experience == 5.0
    assert item.name == "python"


def test_parsed_cv_result_normalization():
    res = ParsedCVResult.model_validate({
        "candidate_summary": "Summary text",
        "extracted_skills": [  # алиас extracted_skills -> skills
            {"skill_id": "langgraph", "name": "LangGraph", "category_id": "ai_agentic", "years_experience": 2}
        ]
    })
    assert len(res.skills) == 1
    assert res.skills[0].name == "LangGraph"


def test_unwrap_structured_output():
    env1 = {"structured_output": {"foo": "bar"}}
    assert unwrap_structured_output(env1) == {"foo": "bar"}

    env2 = {"response": '{"num": 42}'}
    assert unwrap_structured_output(env2) == {"num": 42}

