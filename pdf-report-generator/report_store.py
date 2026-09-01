from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_DATABASE = ROOT / "report.db"


def ensure_reports_table(
    database: Path = DEFAULT_DATABASE,
) -> None:
    database = database.resolve()

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def create_report_record(
    path: str,
    database: Path = DEFAULT_DATABASE,
) -> dict[str, Any]:
    database = database.resolve()
    created_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(database) as connection:
        cursor = connection.execute(
            """
            INSERT INTO reports (path, created_at)
            VALUES (?, ?)
            """,
            (path, created_at),
        )
        report_id = int(cursor.lastrowid)
        connection.commit()

    return {
        "id": report_id,
        "path": path,
        "created_at": created_at,
    }


def get_report_record(
    report_id: int,
    database: Path = DEFAULT_DATABASE,
) -> dict[str, Any] | None:
    database = database.resolve()

    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT id, path, created_at
            FROM reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": int(row["id"]),
        "path": str(row["path"]),
        "created_at": str(row["created_at"]),
    }