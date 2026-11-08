"""DDL схемы SQLite, мягкие миграции колонок и первичный засев данных."""
import json
import sqlite3
from datetime import datetime, timezone

from job_filter.db.seed_data import (
    DEFAULT_BLACKLISTED_BOARDS,
    DEFAULT_CANDIDATE_SKILLS,
    DEFAULT_GEO_PREFERENCES,
    DEFAULT_SKILL_CATEGORIES,
)

SKILLS_SEEDED_KEY = "skills_seeded_v1"

_DDL = (
    """
    CREATE TABLE IF NOT EXISTS processed_jobs (
        job_id TEXT PRIMARY KEY,
        site TEXT DEFAULT 'linkedin',
        title TEXT,
        company TEXT,
        url TEXT,
        date_posted TEXT,
        seniority_level TEXT,
        employment_type TEXT,
        job_function TEXT,
        industry TEXT,
        salary TEXT,
        description TEXT,
        matched INTEGER,
        reject_reason TEXT,
        processed_at TEXT,
        enrichment_json TEXT,
        score INTEGER,
        tier TEXT,
        score_details_json TEXT,
        user_status TEXT DEFAULT 'new',
        user_reject_reason TEXT,
        application_stage TEXT,
        company_reject_reason TEXT,
        application_email_url TEXT,
        application_updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS blacklisted_boards (
        domain TEXT PRIMARY KEY,
        reason TEXT,
        created_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS company_ats_map (
        company_key TEXT PRIMARY KEY,
        company_name TEXT,
        ats_domain TEXT,
        sample_url TEXT,
        updated_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS candidate_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        profile_text TEXT,
        cv_text TEXT,
        geo_preferences_json TEXT,
        updated_at TEXT
    )
    """,
    # Категории и матрица навыков для гибкого скоринга
    """
    CREATE TABLE IF NOT EXISTS skill_categories (
        category_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        multiplier REAL DEFAULT 2.0,
        max_points INTEGER DEFAULT 30,
        sort_order INTEGER DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS candidate_skills (
        skill_id TEXT PRIMARY KEY,
        category_id TEXT NOT NULL,
        name TEXT NOT NULL,
        years_experience REAL DEFAULT 0.0,
        weight_points INTEGER DEFAULT 0,
        is_primary INTEGER DEFAULT 0,
        aliases_json TEXT,
        FOREIGN KEY (category_id) REFERENCES skill_categories(category_id)
    )
    """,
    # Системные метаданные (в т.ч. флаг, предотвращающий повторный автозасев после ручного удаления)
    """
    CREATE TABLE IF NOT EXISTS app_metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """,
)

# Колонки, добавленные в processed_jobs после первой версии схемы
_PROCESSED_JOBS_MIGRATIONS = {
    "site": "TEXT DEFAULT 'linkedin'",
    "location": "TEXT",
    "is_remote": "INTEGER",
    "seniority_level": "TEXT",
    "employment_type": "TEXT",
    "job_function": "TEXT",
    "industry": "TEXT",
    "salary": "TEXT",
    "description": "TEXT",
    "reject_reason": "TEXT",
    "enrichment_json": "TEXT",
    "score": "INTEGER",
    "tier": "TEXT",
    "score_details_json": "TEXT",
    "user_status": "TEXT DEFAULT 'new'",
    "apply_url": "TEXT",
    "ats_domain": "TEXT",
    "user_reject_reason": "TEXT",
    "application_stage": "TEXT",
    "company_reject_reason": "TEXT",
    "application_email_url": "TEXT",
    "application_updated_at": "TEXT",
}


def apply_schema(conn: sqlite3.Connection) -> None:
    for ddl in _DDL:
        conn.execute(ddl)

    existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(processed_jobs)").fetchall()}
    for col_name, col_type in _PROCESSED_JOBS_MIGRATIONS.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE processed_jobs ADD COLUMN {col_name} {col_type}")

    # Мягкая миграция для candidate_settings
    cand_cols = {row[1] for row in conn.execute("PRAGMA table_info(candidate_settings)").fetchall()}
    if "geo_preferences_json" not in cand_cols:
        conn.execute("ALTER TABLE candidate_settings ADD COLUMN geo_preferences_json TEXT")

    # Индексы для ускорения фильтрации по вкладкам, статусам и компаниям
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_jobs_status_matched_score "
        "ON processed_jobs (user_status, matched, score DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_jobs_processed_at "
        "ON processed_jobs (processed_at DESC)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_jobs_company "
        "ON processed_jobs ( lower(trim(company)) )"
    )


def seed_initial_data(conn: sqlite3.Connection) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    geo_default_json = json.dumps(DEFAULT_GEO_PREFERENCES, ensure_ascii=False)

    conn.executemany(
        "INSERT OR IGNORE INTO blacklisted_boards (domain, reason, created_at) VALUES (?, ?, ?)",
        [(dom, rsn, now_iso) for dom, rsn in DEFAULT_BLACKLISTED_BOARDS],
    )
    conn.execute(
        "INSERT OR IGNORE INTO candidate_settings (id, profile_text, cv_text, geo_preferences_json, updated_at) "
        "VALUES (1, '', '', ?, ?)",
        (geo_default_json, now_iso),
    )
    # Если строка уже есть, но geo_preferences_json пустой — инициализируем дефолтом
    conn.execute(
        "UPDATE candidate_settings SET geo_preferences_json = ? WHERE id = 1 AND (geo_preferences_json IS NULL OR geo_preferences_json = '')",
        (geo_default_json,),
    )

    # Стартовые категории и навыки засеваются ТОЛЬКО один раз — при первом запуске
    is_seeded = conn.execute("SELECT value FROM app_metadata WHERE key = ?", (SKILLS_SEEDED_KEY,)).fetchone()
    if is_seeded:
        return
    cat_count = conn.execute("SELECT COUNT(*) FROM skill_categories").fetchone()[0]
    if cat_count == 0:
        conn.executemany(
            "INSERT OR IGNORE INTO skill_categories (category_id, title, multiplier, max_points, sort_order) "
            "VALUES (:category_id, :title, :multiplier, :max_points, :sort_order)",
            DEFAULT_SKILL_CATEGORIES,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO candidate_skills "
            "(skill_id, category_id, name, years_experience, weight_points, is_primary, aliases_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    s["skill_id"], s["category_id"], s["name"], s["years_experience"],
                    s["weight_points"], s["is_primary"], json.dumps(s["aliases"], ensure_ascii=False),
                )
                for s in DEFAULT_CANDIDATE_SKILLS
            ],
        )
    conn.execute("INSERT OR REPLACE INTO app_metadata (key, value) VALUES (?, '1')", (SKILLS_SEEDED_KEY,))

