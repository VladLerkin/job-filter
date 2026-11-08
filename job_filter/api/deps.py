"""Зависимости FastAPI (инъекция соединения с БД)."""
from collections.abc import Iterator
import sqlite3

from job_filter.db.connection import connect


def get_db() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

