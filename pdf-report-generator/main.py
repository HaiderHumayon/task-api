from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from pdf_renderer import generate_pdf
from report_store import (
    DEFAULT_DATABASE,
    create_report_record,
    ensure_reports_table,
    get_report_record,
)


ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    ensure_reports_table(DEFAULT_DATABASE)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="PDF Report Generator",
    version="0.4.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/reports",
    status_code=status.HTTP_201_CREATED,
)
def create_report() -> dict[str, object]:
    ensure_reports_table(DEFAULT_DATABASE)

    # Reserve a row first so its numeric id becomes the stable filename.
    provisional = create_report_record(
        path="pending",
        database=DEFAULT_DATABASE,
    )
    report_id = int(provisional["id"])

    relative_path = f"reports/{report_id}.pdf"
    output_path = ROOT / relative_path

    try:
        generate_pdf(
            output_path=output_path,
            database=DEFAULT_DATABASE,
        )
    except Exception:
        # The API should not leave a database row pointing at a missing file.
        import sqlite3

        with sqlite3.connect(DEFAULT_DATABASE) as connection:
            connection.execute(
                "DELETE FROM reports WHERE id = ?",
                (report_id,),
            )
            connection.commit()

        raise

    import sqlite3

    with sqlite3.connect(DEFAULT_DATABASE) as connection:
        connection.execute(
            """
            UPDATE reports
            SET path = ?
            WHERE id = ?
            """,
            (relative_path, report_id),
        )
        connection.commit()

    record = get_report_record(
        report_id,
        database=DEFAULT_DATABASE,
    )

    if record is None:
        raise RuntimeError("Report metadata disappeared after creation")

    return {
        "id": report_id,
        "created_at": record["created_at"],
        "file_url": f"/reports/{report_id}/file",
    }


@app.get("/reports/{report_id}")
def get_report(report_id: int) -> dict[str, object]:
    record = get_report_record(
        report_id,
        database=DEFAULT_DATABASE,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    return {
        "id": record["id"],
        "path": record["path"],
        "created_at": record["created_at"],
        "file_url": f"/reports/{report_id}/file",
    }


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int) -> FileResponse:
    record = get_report_record(
        report_id,
        database=DEFAULT_DATABASE,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    path = ROOT / str(record["path"])

    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found",
        )

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=f"bookstore-report-{report_id}.pdf",
    )