"""SQL-доступ к профилю кандидата (таблица candidate_settings, одна строка id=1)."""
import sqlite3
from datetime import datetime, timezone


def get_settings(conn: sqlite3.Connection) -> dict[str, str]:
    row = conn.execute("SELECT profile_text, cv_text, updated_at FROM candidate_settings WHERE id = 1").fetchone()
    if not row:
        return {"profile_text": "", "cv_text": "", "updated_at": ""}
    return {
        "profile_text": row["profile_text"] or "",
        "cv_text": row["cv_text"] or "",
        "updated_at": row["updated_at"] or "",
    }


def save_settings(conn: sqlite3.Connection, profile_text: str, cv_text: str) -> dict[str, str]:
    now_iso = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO candidate_settings (id, profile_text, cv_text, updated_at)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            profile_text = excluded.profile_text,
            cv_text = excluded.cv_text,
            updated_at = excluded.updated_at
        """,
        (profile_text, cv_text, now_iso),
    )
    return {"profile_text": profile_text, "cv_text": cv_text, "updated_at": now_iso}

