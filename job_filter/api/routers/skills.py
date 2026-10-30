"""Роуты управления матрицей навыков и категориями скоринга."""
import sqlite3
from fastapi import APIRouter, Depends

from job_filter.api.deps import get_db
from job_filter.api.schemas import CandidateSkillRequest, SkillCategoryRequest
from job_filter.services import skills_service

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/matrix")
def get_skills_matrix(conn: sqlite3.Connection = Depends(get_db)):
    return skills_service.get_matrix_data(conn)


@router.post("/category")
def upsert_skill_category(
    body: SkillCategoryRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    return skills_service.save_category(
        conn,
        category_id=body.category_id,
        title=body.title,
        multiplier=body.multiplier,
        max_points=body.max_points,
        sort_order=body.sort_order,
    )


@router.delete("/category/{category_id:path}")
def remove_skill_category(
    category_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    deleted_id = skills_service.delete_category(conn, category_id)
    return {"status": "ok", "deleted_category_id": deleted_id}


@router.post("/item")
def upsert_candidate_skill(
    body: CandidateSkillRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    return skills_service.save_skill(
        conn,
        skill_id=body.skill_id,
        category_id=body.category_id,
        name=body.name,
        years_experience=body.years_experience,
        weight_points=body.weight_points,
        is_primary=body.is_primary,
        aliases=body.aliases,
    )


@router.delete("/item/{skill_id:path}")
def remove_candidate_skill(
    skill_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    deleted_id = skills_service.delete_skill(conn, skill_id)
    return {"status": "ok", "deleted_skill_id": deleted_id}


@router.post("/reset-defaults")
def reset_skills_defaults(conn: sqlite3.Connection = Depends(get_db)):
    res = skills_service.reset_to_defaults(conn)
    return {"status": "ok", **res}
