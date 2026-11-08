"""SQL-доступ к вакансиям (таблица processed_jobs)."""
import sqlite3
from datetime import datetime, timezone
from typing import Any

_JOB_COLUMNS = (
    "job_id", "site", "location", "is_remote", "title", "company", "url", "date_posted",
    "seniority_level", "employment_type", "job_function", "industry", "salary",
    "description", "matched", "reject_reason", "processed_at",
    "enrichment_json", "score", "tier", "score_details_json", "user_status",
    "apply_url", "ats_domain", "user_reject_reason",
    "application_stage", "company_reject_reason", "application_email_url", "application_updated_at",
)


def get_processed_ids(conn: sqlite3.Connection) -> set[str]:
    return {row[0] for row in conn.execute("SELECT job_id FROM processed_jobs")}


def get_job(conn: sqlite3.Connection, job_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM processed_jobs WHERE job_id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def replace_job(conn: sqlite3.Connection, record: dict[str, Any]) -> None:
    """INSERT OR REPLACE полной записи вакансии. Отсутствующие поля записываются как NULL."""
    record = {**record, "processed_at": record.get("processed_at") or datetime.now(timezone.utc).isoformat()}
    cols = ", ".join(_JOB_COLUMNS)
    placeholders = ", ".join("?" for _ in _JOB_COLUMNS)
    conn.execute(
        f"INSERT OR REPLACE INTO processed_jobs ({cols}) VALUES ({placeholders})",
        tuple(record.get(c) for c in _JOB_COLUMNS),
    )


def update_enrichment_and_score(
    conn: sqlite3.Connection,
    job_id: str,
    enrichment_json: str,
    score: int,
    tier: str,
    score_details_json: str,
    matched: int,
    reject_reason: str | None,
) -> None:
    conn.execute(
        """
        UPDATE processed_jobs
        SET enrichment_json = ?,
            score = ?,
            tier = ?,
            score_details_json = ?,
            matched = ?,
            reject_reason = ?
        WHERE job_id = ?
        """,
        (enrichment_json, score, tier, score_details_json, matched, reject_reason, job_id),
    )


def set_user_status(
    conn: sqlite3.Connection,
    job_id: str,
    user_status: str,
    user_reject_reason: str | None = None,
) -> int:
    if user_reject_reason is not None or user_status == "rejected":
        cur = conn.execute(
            "UPDATE processed_jobs SET user_status = ?, user_reject_reason = ? WHERE job_id = ?",
            (user_status, user_reject_reason, job_id),
        )
    elif user_status == "applied":
        now_iso = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            """
            UPDATE processed_jobs
            SET user_status = ?,
                application_stage = COALESCE(application_stage, 'applied'),
                application_updated_at = COALESCE(application_updated_at, ?)
            WHERE job_id = ?
            """,
            (user_status, now_iso, job_id),
        )
    elif user_status in ("new", "saved"):
        cur = conn.execute(
            """
            UPDATE processed_jobs
            SET user_status = ?,
                user_reject_reason = NULL,
                application_stage = CASE WHEN ? = 'new' THEN NULL ELSE application_stage END,
                company_reject_reason = CASE WHEN ? = 'new' THEN NULL ELSE company_reject_reason END,
                application_email_url = CASE WHEN ? = 'new' THEN NULL ELSE application_email_url END,
                application_updated_at = CASE WHEN ? = 'new' THEN NULL ELSE application_updated_at END
            WHERE job_id = ?
            """,
            (user_status, user_status, user_status, user_status, user_status, job_id),
        )
    else:
        cur = conn.execute(
            "UPDATE processed_jobs SET user_status = ? WHERE job_id = ?",
            (user_status, job_id),
        )
    return cur.rowcount


def set_application_stage(
    conn: sqlite3.Connection,
    job_id: str,
    application_stage: str,
    company_reject_reason: str | None = None,
    application_email_url: str | None = None,
) -> int:
    """Обновляет этап отклика (applied | confirmed | interview | rejected_by_company), причину/детали и ссылку на письмо."""
    now_iso = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        """
        UPDATE processed_jobs
        SET user_status = 'applied',
            application_stage = ?,
            company_reject_reason = ?,
            application_email_url = COALESCE(?, application_email_url),
            application_updated_at = ?
        WHERE job_id = ?
        """,
        (application_stage, company_reject_reason, application_email_url, now_iso, job_id),
    )
    return cur.rowcount


def list_applied_jobs(conn: sqlite3.Connection) -> list[dict]:
    """Возвращает все вакансии со статусом applied."""
    cur = conn.execute(
        """
        SELECT job_id, site, location, is_remote, title, company, url, date_posted,
               processed_at, score, tier, user_status, apply_url, ats_domain,
               application_stage, company_reject_reason, application_email_url, application_updated_at
        FROM processed_jobs
        WHERE user_status = 'applied'
        ORDER BY processed_at DESC
        """
    )
    return [dict(r) for r in cur.fetchall()]


def get_user_rejected_jobs(conn: sqlite3.Connection) -> list[dict]:
    """Возвращает список вакансий, отклоненных пользователем с указанием причины."""
    cur = conn.execute(
        """
        SELECT job_id, site, location, is_remote, title, company, url,
               enrichment_json, score, tier, score_details_json,
               user_status, user_reject_reason, description, processed_at
        FROM processed_jobs
        WHERE user_status = 'rejected' OR (user_reject_reason IS NOT NULL AND user_reject_reason != '')
        ORDER BY processed_at DESC
        """
    )
    return [dict(r) for r in cur.fetchall()]


def list_all(conn: sqlite3.Connection, include_description: bool = False) -> list[dict]:
    if include_description:
        return [dict(r) for r in conn.execute("SELECT * FROM processed_jobs ORDER BY processed_at DESC")]
    return [
        dict(r)
        for r in conn.execute(
            """
            SELECT job_id, site, location, is_remote, title, company, url, date_posted,
                   seniority_level, employment_type, job_function, industry, salary,
                   (description IS NOT NULL AND description != '') AS has_description,
                   matched, reject_reason, processed_at,
                   enrichment_json, score, tier, score_details_json, user_status,
                   apply_url, ats_domain, user_reject_reason,
                   application_stage, company_reject_reason, application_email_url, application_updated_at
            FROM processed_jobs
            ORDER BY processed_at DESC
            """
        )
    ]


def get_job_description(conn: sqlite3.Connection, job_id: str) -> str | None:
    row = conn.execute("SELECT description FROM processed_jobs WHERE job_id = ?", (job_id,)).fetchone()
    return row["description"] if row else None


def list_pending_enrichment(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    """Вакансии с описанием, прошедшие базовый фильтр, но ещё не обогащённые LLM."""
    return conn.execute(
        """
        SELECT job_id, title, company, location, is_remote, url, date_posted, seniority_level, industry, salary, description
        FROM processed_jobs
        WHERE description IS NOT NULL
          AND description != ''
          AND enrichment_json IS NULL
          AND (reject_reason IS NULL OR reject_reason = '')
        ORDER BY processed_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def list_enriched(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT job_id, title, company, location, is_remote, date_posted, seniority_level,
               industry, salary, description, enrichment_json, reject_reason,
               score, tier, matched
        FROM processed_jobs
        WHERE enrichment_json IS NOT NULL
        """
    ).fetchall()


def list_final_matches(conn: sqlite3.Connection, min_score: int) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute(
            """
            SELECT * FROM processed_jobs
            WHERE matched = 1 AND score IS NOT NULL AND score >= ?
            ORDER BY score DESC, date_posted DESC
            """,
            (min_score,),
        )
    ]


def propagate_company_ats(conn: sqlite3.Connection, company_key: str, ats_domain: str, apply_url: str | None) -> None:
    """Проставляет ATS-домен (и apply_url) всем вакансиям компании, где они ещё не заданы."""
    conn.execute(
        """
        UPDATE processed_jobs
        SET ats_domain = COALESCE(ats_domain, ?),
            apply_url = COALESCE(apply_url, ?)
        WHERE lower(trim(company)) = ?
        """,
        (ats_domain, apply_url, company_key),
    )


def set_job_ats(
    conn: sqlite3.Connection,
    job_id: str,
    ats_domain: str | None,
    apply_url: str | None,
    hide_with_reason: str | None = None,
) -> None:
    """Обновляет ATS-домен/ссылку вакансии; если задан hide_with_reason — скрывает вакансию."""
    if hide_with_reason is not None:
        conn.execute(
            """
            UPDATE processed_jobs
            SET user_status = 'hidden',
                ats_domain = COALESCE(?, ats_domain),
                apply_url = COALESCE(?, apply_url),
                reject_reason = COALESCE(reject_reason, ?)
            WHERE job_id = ?
            """,
            (ats_domain, apply_url, hide_with_reason, job_id),
        )
    else:
        conn.execute(
            """
            UPDATE processed_jobs
            SET ats_domain = COALESCE(?, ats_domain),
                apply_url = COALESCE(?, apply_url)
            WHERE job_id = ?
            """,
            (ats_domain, apply_url, job_id),
        )

