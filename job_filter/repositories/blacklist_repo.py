"""SQL-доступ к чёрному списку ATS-сайтов (blacklisted_boards) и привязкам компания -> ATS (company_ats_map)."""
import sqlite3


def list_boards(conn: sqlite3.Connection) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute("SELECT domain, reason, created_at FROM blacklisted_boards ORDER BY created_at DESC")
    ]


def list_companies(conn: sqlite3.Connection) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute(
            "SELECT company_key, company_name, ats_domain, sample_url, updated_at FROM company_ats_map "
            "ORDER BY updated_at DESC"
        )
    ]


def list_board_domains(conn: sqlite3.Connection) -> list[str]:
    return [r["domain"] for r in conn.execute("SELECT domain FROM blacklisted_boards")]


def get_board_reasons(conn: sqlite3.Connection) -> dict[str, str | None]:
    """domain(lower) -> reason (может быть None)."""
    return {r["domain"].lower(): r["reason"] for r in conn.execute("SELECT domain, reason FROM blacklisted_boards")}


def upsert_board(conn: sqlite3.Connection, domain: str, reason: str, created_at: str) -> None:
    conn.execute(
        """
        INSERT INTO blacklisted_boards (domain, reason, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(domain) DO UPDATE SET reason = excluded.reason
        """,
        (domain, reason, created_at),
    )


def insert_board_if_absent(conn: sqlite3.Connection, domain: str, reason: str, created_at: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO blacklisted_boards (domain, reason, created_at) VALUES (?, ?, ?)",
        (domain, reason, created_at),
    )


def delete_board(conn: sqlite3.Connection, domain: str) -> None:
    conn.execute("DELETE FROM blacklisted_boards WHERE lower(domain) = ?", (domain,))


def get_company_ats(conn: sqlite3.Connection, company_key: str) -> dict | None:
    row = conn.execute(
        "SELECT company_name, ats_domain, sample_url, updated_at FROM company_ats_map WHERE company_key = ?",
        (company_key,),
    ).fetchone()
    return dict(row) if row else None


def get_company_ats_domains(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["company_key"]: r["ats_domain"] for r in conn.execute("SELECT company_key, ats_domain FROM company_ats_map")}


def upsert_company_ats(
    conn: sqlite3.Connection,
    company_key: str,
    company_name: str,
    ats_domain: str,
    sample_url: str | None,
    updated_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO company_ats_map (company_key, company_name, ats_domain, sample_url, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(company_key) DO UPDATE SET
            ats_domain = excluded.ats_domain,
            sample_url = COALESCE(excluded.sample_url, company_ats_map.sample_url),
            updated_at = excluded.updated_at
        """,
        (company_key, company_name, ats_domain, sample_url, updated_at),
    )


def delete_company_ats(conn: sqlite3.Connection, company_key: str) -> None:
    conn.execute("DELETE FROM company_ats_map WHERE company_key = ?", (company_key,))

