"""Сервис управления категориями и навыками кандидата, сброса к базовым и пересчёта скоринга."""
import logging
import sqlite3

from job_filter import config
from job_filter.db.seed_data import default_skill_matrix
from job_filter.models.enrichment import JobEnrichment
from job_filter.repositories import candidate_repo, jobs_repo, skills_repo
from job_filter.scoring.matrix import calculate_skill_points, get_skill_matrix, invalidate_matrix_cache
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
    rows = conn.execute("SELECT skill_id, years_experience FROM candidate_skills WHERE category_id = ?", (cid,)).fetchall()
    for r in rows:
        new_pts = calculate_skill_points(float(r["years_experience"]), multiplier, max_points)
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
            weight_points = calculate_skill_points(
                years_experience, float(cat["multiplier"]), int(cat["max_points"])
            )
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
    """Пересчитывает скоры всех уже обогащённых вакансий по текущей матрице навыков и гео-правилам."""
    rows = jobs_repo.list_enriched(conn)
    matrix = get_skill_matrix(conn)
    settings = candidate_repo.get_settings(conn)
    geo_preferences = settings.get("geo_preferences")
    updated = 0
    for r in rows:
        try:
            enrichment = JobEnrichment.model_validate_json(r["enrichment_json"])
            job_loc = r["location"] if ("location" in r.keys() and r["location"]) else None
            is_rem_val = r["is_remote"] if ("is_remote" in r.keys() and r["is_remote"] is not None) else None
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
                geo_preferences=geo_preferences,
                job_location=job_loc,
                is_remote=is_rem_val,
            )
            old_rr = r["reject_reason"] if "reject_reason" in r.keys() else None
            if not score_res.geo_passed:
                reject_reason = score_res.geo_reject_reason
                matched = 0
            elif score_res.score < config.FAIR_SCORE_THRESHOLD:
                reject_reason = f"low_score:{score_res.score}"
                matched = 0
            else:
                if old_rr and old_rr.startswith("bad_board:"):
                    reject_reason = old_rr
                    matched = 0
                else:
                    reject_reason = None
                    matched = 1

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


def preview_rescore_diff(conn: sqlite3.Connection) -> dict:
    """Сухой прогон пересчёта скоринга в памяти без записи в БД. Возвращает список изменений."""
    rows = jobs_repo.list_enriched(conn)
    matrix = get_skill_matrix(conn)
    settings = candidate_repo.get_settings(conn)
    geo_preferences = settings.get("geo_preferences")

    promoted: list[dict] = []
    demoted: list[dict] = []
    score_changed: list[dict] = []

    for r in rows:
        try:
            enrichment = JobEnrichment.model_validate_json(r["enrichment_json"])
            job_loc = r["location"] if ("location" in r.keys() and r["location"]) else None
            is_rem_val = r["is_remote"] if ("is_remote" in r.keys() and r["is_remote"] is not None) else None
            old_score = r["score"] if "score" in r.keys() else None
            old_tier = r["tier"] if "tier" in r.keys() else None
            old_matched = r["matched"] if "matched" in r.keys() else 0
            old_rr = r["reject_reason"] if "reject_reason" in r.keys() else None

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
                geo_preferences=geo_preferences,
                job_location=job_loc,
                is_remote=is_rem_val,
            )

            if not score_res.geo_passed:
                new_rr = score_res.geo_reject_reason
                new_matched = 0
            elif score_res.score < config.FAIR_SCORE_THRESHOLD:
                new_rr = f"low_score:{score_res.score}"
                new_matched = 0
            else:
                if old_rr and old_rr.startswith("bad_board:"):
                    new_rr = old_rr
                    new_matched = 0
                else:
                    new_rr = None
                    new_matched = 1

            diff_item = {
                "job_id": r["job_id"],
                "title": r["title"],
                "company": r["company"],
                "old_score": old_score,
                "new_score": score_res.score,
                "old_tier": old_tier,
                "new_tier": score_res.tier,
                "old_matched": old_matched,
                "new_matched": new_matched,
                "old_reject_reason": old_rr,
                "new_reject_reason": new_rr,
            }
            if old_matched == 0 and new_matched == 1:
                promoted.append(diff_item)
            elif old_matched == 1 and new_matched == 0:
                demoted.append(diff_item)
            elif old_score != score_res.score or old_tier != score_res.tier or old_rr != new_rr:
                score_changed.append(diff_item)
        except Exception:
            continue

    return {
        "total_evaluated": len(rows),
        "promoted_to_matched": promoted,
        "demoted_to_rejected": demoted,
        "other_changes": score_changed,
    }

