"""Сервис управления категориями и навыками кандидата, сброса к базовым и пересчёта скоринга."""
import logging
import sqlite3

from job_filter.db.seed_data import default_skill_matrix
from job_filter.models.enrichment import JobEnrichment
from job_filter.repositories import jobs_repo, skills_repo
from job_filter.scoring.matrix import get_skill_matrix, invalidate_matrix_cache
from job_filter.scoring.scorer import score_vacancy_by_skill

logger = logging.getLogger(__name__)


def get_matrix_data(conn: sqlite3.Connection) -> dict:
    return skills_repo.get_matrix(conn)


def save_category(
    conn: sqlite3.Connection,
    category_id: str,
    title: str,
    multiplier: float = 2.0,
    max_points: int = 30,
    sort_order: int = 0,
) -> dict:
    cid = category_id.strip().lower()
    t = title.strip()
    skills_repo.upsert_category(conn, cid, t, multiplier, max_points, sort_order)
    # При обновлении множителя/лимита категории автоматически пересчитываем баллы входящих в неё навыков
    if multiplier >= 0:
        rows = conn.execute("SELECT skill_id, years_experience FROM candidate_skills WHERE category_id = ?", (cid,)).fetchall()
        for r in rows:
            new_pts = min(round(float(r["years_experience"]) * multiplier), max_points)
            conn.execute("UPDATE candidate_skills SET weight_points = ? WHERE skill_id = ?", (new_pts, r["skill_id"]))
    conn.commit()
    invalidate_matrix_cache()
    return {"category_id": cid, "title": t, "multiplier": multiplier, "max_points": max_points, "sort_order": sort_order}


def delete_category(conn: sqlite3.Connection, category_id: str) -> str:
    cid = category_id.strip().lower()
    skills_repo.delete_category_with_skills(conn, cid)
    conn.commit()
    invalidate_matrix_cache()
    return cid


def save_skill(
    conn: sqlite3.Connection,
    skill_id: str,
    category_id: str,
    name: str,
    years_experience: float = 0.0,
    weight_points: int | None = None,
    is_primary: bool = False,
    aliases: list[str] | None = None,
) -> dict:
    sid = skill_id.strip().lower()
    cid = category_id.strip().lower()
    name_clean = name.strip()

    if weight_points is None:
        cat = skills_repo.get_category(conn, cid)
        if cat:
            mult = float(cat["multiplier"])
            max_p = int(cat["max_points"])
            if mult < 0:
                calc = max_p
            else:
                calc = round(years_experience * mult)
                calc = min(calc, max_p)
            weight_points = int(calc)
        else:
            weight_points = int(years_experience * 2)

    aliases_list = [a.strip().lower() for a in (aliases or []) if a.strip()]
    if name_clean.lower() not in aliases_list:
        aliases_list.append(name_clean.lower())

    skills_repo.upsert_skill(
        conn,
        skill_id=sid,
        category_id=cid,
        name=name_clean,
        years_experience=years_experience,
        weight_points=weight_points,
        is_primary=is_primary,
        aliases=aliases_list,
    )
    conn.commit()
    invalidate_matrix_cache()
    return {
        "skill_id": sid,
        "category_id": cid,
        "name": name_clean,
        "years_experience": years_experience,
        "weight_points": weight_points,
        "is_primary": is_primary,
        "aliases": aliases_list,
    }


def delete_skill(conn: sqlite3.Connection, skill_id: str) -> str:
    sid = skill_id.strip().lower()
    skills_repo.delete_skill(conn, sid)
    conn.commit()
    invalidate_matrix_cache()
    return sid


def reset_to_defaults(conn: sqlite3.Connection) -> dict:
    defaults = default_skill_matrix()
    for c in defaults["categories"]:
        skills_repo.upsert_category(conn, c["category_id"], c["title"], c["multiplier"], c["max_points"], c["sort_order"])
    for s in defaults["skills"]:
        skills_repo.upsert_skill(
            conn,
            skill_id=s["skill_id"],
            category_id=s["category_id"],
            name=s["name"],
            years_experience=s["years_experience"],
            weight_points=s["weight_points"],
            is_primary=bool(s.get("is_primary", 0)),
            aliases=s.get("aliases", []),
        )
    conn.commit()
    invalidate_matrix_cache()
    return {"categories_count": len(defaults["categories"]), "skills_count": len(defaults["skills"])}


def rescore_all_jobs(conn: sqlite3.Connection) -> int:
    """Пересчитывает скоры всех уже обогащённых вакансий по текущей матрице навыков."""
    rows = jobs_repo.list_enriched(conn)
    matrix = get_skill_matrix(conn)
    updated = 0
    for r in rows:
        try:
            enrichment = JobEnrichment.model_validate_json(r["enrichment_json"])
            score_res = score_vacancy_by_skill(
                title=r["title"] or "",
                company=r["company"],
                date_posted=r["date_posted"],
                seniority_level=r["seniority_level"],
                industry=r["industry"],
                salary_text=r["salary"],
                description=r["description"] or "",
                enrichment=enrichment,
                conn=conn,
                matrix=matrix,
            )
            matched = 0 if (not score_res.geo_passed or score_res.score < 50) else 1
            reject_reason = (
                score_res.geo_reject_reason if not score_res.geo_passed else (f"low_score:{score_res.score}" if score_res.score < 50 else None)
            )
            jobs_repo.update_enrichment_and_score(
                conn,
                job_id=r["job_id"],
                enrichment_json=enrichment.model_dump_json(),
                score=score_res.score,
                tier=score_res.tier,
                score_details_json=score_res.model_dump_json(),
                matched=matched,
                reject_reason=reject_reason,
            )
            updated += 1
        except Exception as e:
            logger.debug("Failed to rescore job %s: %s", r["job_id"], e)
            continue
    conn.commit()
    return updated

