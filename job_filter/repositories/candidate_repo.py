"""SQL-доступ к профилю кандидата (таблица candidate_settings, одна строка id=1)."""
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from job_filter.db.seed_data import DEFAULT_GEO_PREFERENCES


def get_settings(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        "SELECT profile_text, cv_text, geo_preferences_json, updated_at FROM candidate_settings WHERE id = 1"
    ).fetchone()
    if not row:
        return {
            "profile_text": "",
            "cv_text": "",
            "geo_preferences": dict(DEFAULT_GEO_PREFERENCES),
            "updated_at": "",
        }

    if hasattr(row, "keys"):
        p_text = row["profile_text"] or ""
        c_text = row["cv_text"] or ""
        geo_raw = row["geo_preferences_json"]
        u_at = row["updated_at"] or ""
    else:
        p_text = (row[0] or "") if len(row) > 0 else ""
        c_text = (row[1] or "") if len(row) > 1 else ""
        geo_raw = row[2] if len(row) > 2 else None
        u_at = (row[3] or "") if len(row) > 3 else ""

    geo_prefs = None
    if geo_raw:
        try:
            geo_prefs = json.loads(geo_raw)
        except Exception:
            pass

    if not isinstance(geo_prefs, dict):
        geo_prefs = dict(DEFAULT_GEO_PREFERENCES)

    return {
        "profile_text": p_text,
        "cv_text": c_text,
        "geo_preferences": geo_prefs,
        "updated_at": u_at,
    }


def save_settings(
    conn: sqlite3.Connection,
    profile_text: str,
    cv_text: str,
    geo_preferences: dict | str | None = None,
) -> dict[str, Any]:
    now_iso = datetime.now(timezone.utc).isoformat()
    if geo_preferences is None:
        current = get_settings(conn)
        geo_dict = current.get("geo_preferences") or DEFAULT_GEO_PREFERENCES
    elif isinstance(geo_preferences, str):
        try:
            geo_dict = json.loads(geo_preferences)
        except Exception:
            geo_dict = dict(DEFAULT_GEO_PREFERENCES)
    elif isinstance(geo_preferences, dict):
        geo_dict = geo_preferences
    else:
        geo_dict = dict(DEFAULT_GEO_PREFERENCES)

    geo_json = json.dumps(geo_dict, ensure_ascii=False)

    conn.execute(
        """
        INSERT INTO candidate_settings (id, profile_text, cv_text, geo_preferences_json, updated_at)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            profile_text = excluded.profile_text,
            cv_text = excluded.cv_text,
            geo_preferences_json = excluded.geo_preferences_json,
            updated_at = excluded.updated_at
        """,
        (profile_text, cv_text, geo_json, now_iso),
    )
    return {
        "profile_text": profile_text,
        "cv_text": cv_text,
        "geo_preferences": geo_dict,
        "updated_at": now_iso,
    }


