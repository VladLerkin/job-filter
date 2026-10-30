"""Загрузка, кэширование и матчинг навыков по матрице скоринга."""
import re
import sqlite3

from job_filter.db.connection import connect
from job_filter.db.seed_data import default_skill_matrix
from job_filter.repositories import skills_repo

_MATRIX_CACHE: dict | None = None


def invalidate_matrix_cache() -> None:
    global _MATRIX_CACHE
    _MATRIX_CACHE = None


def get_skill_matrix(conn: sqlite3.Connection | None = None) -> dict:
    global _MATRIX_CACHE
    if _MATRIX_CACHE is not None and conn is None:
        return _MATRIX_CACHE

    should_close = False
    db_conn = conn
    if db_conn is None:
        try:
            db_conn = connect()
            should_close = True
        except Exception:
            return default_skill_matrix()

    try:
        data = skills_repo.get_matrix(db_conn)
        if data and data.get("categories"):
            _MATRIX_CACHE = data
            return data
    except Exception:
        pass
    finally:
        if should_close and db_conn:
            db_conn.close()

    return default_skill_matrix()


def extract_candidate_aliases(matrix: dict) -> set[str]:
    """Извлекает множество всех нормализованных алиасов кандидата из категорий с неотрицательным множителем."""
    categories = matrix.get("categories", [])
    skills = matrix.get("skills", [])
    skills_by_cat: dict[str, list[dict]] = {}
    for s in skills:
        skills_by_cat.setdefault(s["category_id"], []).append(s)

    candidate_aliases: set[str] = set()
    for cat in categories:
        if float(cat.get("multiplier", 1.0)) >= 0:
            for s in skills_by_cat.get(cat["category_id"], []):
                candidate_aliases.add(s["name"].strip().lower())
                for a in s.get("aliases", []):
                    if a and a.strip():
                        candidate_aliases.add(a.strip().lower())

    if not candidate_aliases:
        fallback = default_skill_matrix()
        for s in fallback["skills"]:
            candidate_aliases.add(s["name"].strip().lower())
            for a in s.get("aliases", []):
                if a and a.strip():
                    candidate_aliases.add(a.strip().lower())

    return candidate_aliases


def skill_matches_candidate(skill: str, candidate_aliases: set[str]) -> bool:
    s = skill.strip().lower()
    if not s:
        return True
    if s in candidate_aliases:
        return True
    # Проверка вхождения границ слов (например "Spring Boot 3" -> "spring boot", "AWS Lambda" -> "aws")
    for cand in candidate_aliases:
        if len(cand) >= 3 and re.search(r"\b" + re.escape(cand) + r"\b", s):
            return True
    return False
