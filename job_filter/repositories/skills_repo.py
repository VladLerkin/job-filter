"""SQL-доступ к матрице навыков: таблицы skill_categories и candidate_skills."""
import json
import sqlite3


def _row_to_skill(row: sqlite3.Row) -> dict:
    s = dict(row)
    try:
        s["aliases"] = json.loads(s["aliases_json"]) if s.get("aliases_json") else []
    except Exception:
        s["aliases"] = []
    return s


def get_matrix(conn: sqlite3.Connection) -> dict:
    categories = [
        dict(r)
        for r in conn.execute(
            "SELECT category_id, title, multiplier, max_points, sort_order FROM skill_categories "
            "ORDER BY sort_order ASC, category_id ASC"
        ).fetchall()
    ]
    skills = [
        _row_to_skill(r)
        for r in conn.execute(
            "SELECT skill_id, category_id, name, years_experience, weight_points, is_primary, aliases_json "
            "FROM candidate_skills ORDER BY years_experience DESC, name ASC"
        ).fetchall()
    ]
    return {"categories": categories, "skills": skills}


def get_category(conn: sqlite3.Connection, category_id: str) -> dict | None:
    row = conn.execute(
        "SELECT category_id, title, multiplier, max_points, sort_order FROM skill_categories WHERE category_id = ?",
        (category_id,),
    ).fetchone()
    return dict(row) if row else None


def upsert_category(
    conn: sqlite3.Connection,
    category_id: str,
    title: str,
    multiplier: float,
    max_points: int,
    sort_order: int,
) -> None:
    conn.execute(
        """
        INSERT INTO skill_categories (category_id, title, multiplier, max_points, sort_order)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(category_id) DO UPDATE SET
            title = excluded.title,
            multiplier = excluded.multiplier,
            max_points = excluded.max_points,
            sort_order = excluded.sort_order
        """,
        (category_id, title, multiplier, max_points, sort_order),
    )


def delete_category_with_skills(conn: sqlite3.Connection, category_id: str) -> None:
    conn.execute("DELETE FROM candidate_skills WHERE category_id = ?", (category_id,))
    conn.execute("DELETE FROM skill_categories WHERE category_id = ?", (category_id,))


def upsert_skill(
    conn: sqlite3.Connection,
    skill_id: str,
    category_id: str,
    name: str,
    years_experience: float,
    weight_points: int,
    is_primary: bool,
    aliases: list[str],
) -> None:
    conn.execute(
        """
        INSERT INTO candidate_skills (skill_id, category_id, name, years_experience, weight_points, is_primary, aliases_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(skill_id) DO UPDATE SET
            category_id = excluded.category_id,
            name = excluded.name,
            years_experience = excluded.years_experience,
            weight_points = excluded.weight_points,
            is_primary = excluded.is_primary,
            aliases_json = excluded.aliases_json
        """,
        (
            skill_id, category_id, name, years_experience, weight_points,
            1 if is_primary else 0, json.dumps(aliases, ensure_ascii=False),
        ),
    )


def delete_skill(conn: sqlite3.Connection, skill_id: str) -> None:
    conn.execute("DELETE FROM candidate_skills WHERE skill_id = ?", (skill_id,))

