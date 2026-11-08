"""Подключение к SQLite.

`init_db()` вызывается один раз при старте приложения/CLI (схема + миграции + засев),
`connect()` — дешёвое открытие соединения для каждого запроса/операции.
"""
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from job_filter import config
from job_filter.db.schema import apply_schema, seed_initial_data


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or config.DB_PATH, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    """Создаёт схему, выполняет мягкие миграции и первичный засев данных."""
    conn = connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        apply_schema(conn)
        seed_initial_data(conn)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def db_session(db_path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """Контекст-менеджер с атомарным коммитом/откатом и гарантированным закрытием соединения."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

