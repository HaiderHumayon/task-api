from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from fastapi import Body, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pdf_renderer import generate_pdf
from report_store import (
    DEFAULT_DATABASE,
    create_report_record,
    delete_report_record,
    ensure_reports_table,
    get_latest_report_for_utc_day,
    get_report_record,
    update_report_path,
)


ROOT = Path(__file__).resolve().parent
REPORTS_DIR = ROOT / "reports"


class ReportRequest(BaseModel):
    force: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    ensure_reports_table(DEFAULT_DATABASE)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="PDF Report Generator",
    version="0.5.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def response_payload(
    record: dict[str, object],
    *,
    reused: bool,
) -> dict[str, object]:
    report_id = int(record["id"])

    return {
        "id": report_id,
        "created_at": record["created_at"],
        "file_url": f"/reports/{report_id}/file",
        "reused": reused,
    }


@app.post("/reports")
def create_report(
    response: Response,
    payload: ReportRequest | None = Body(default=None),
) -> dict[str, object]:
    ensure_reports_table(DEFAULT_DATABASE)

    force = payload.force if payload is not None else False
    today_utc = datetime.now(timezone.utc).date().isoformat()

    if not force:
        existing = get_latest_report_for_utc_day(
            today_utc,
            database=DEFAULT_DATABASE,
        )

        if existing is not None:
            existing_path = ROOT / str(existing["path"])

            if existing_path.is_file():
                response.status_code = status.HTTP_200_OK
                return response_payload(
                    existing,
                    reused=True,
                )

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
        update_report_path(
            report_id,
            relative_path,
            database=DEFAULT_DATABASE,
        )
    except Exception:
        delete_report_record(
            report_id,
            database=DEFAULT_DATABASE,
        )
        output_path.unlink(missing_ok=True)
        raise

    record = get_report_record(
        report_id,
        database=DEFAULT_DATABASE,
    )

    if record is None:
        raise RuntimeError("Report metadata disappeared after creation")

    response.status_code = status.HTTP_201_CREATED

    return response_payload(
        record,
        reused=False,
    )


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