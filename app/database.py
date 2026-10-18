import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from app.config import DATABASE_PATH


def _connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    connection = _connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_consultation(question: str, answer: str) -> tuple[int, str]:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO consultations (question, answer, created_at)
            VALUES (?, ?, ?)
            """,
            (question, answer, created_at),
        )
        return int(cursor.lastrowid), created_at


def get_consultations(limit: int = 20) -> list[dict[str, Any]]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, question, answer, created_at
            FROM consultations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_consultations() -> None:
    with _connection() as connection:
        connection.execute("DELETE FROM consultations")
