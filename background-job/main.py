from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import inngest
import inngest.fast_api


reports: dict[str, dict[str, Any]] = {}


class ReportRequest(BaseModel):
    topic: str


inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
    retries=0,
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep(
        "wait-five-seconds",
        datetime.timedelta(seconds=5),
    )
    return "Hello from the background!"


@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=0,
)
async def make_report(ctx: inngest.Context) -> dict[str, Any]:
    report_id = str(ctx.event.data["id"])
    topic = str(ctx.event.data["topic"])

    await ctx.step.sleep(
        "do-the-slow-work",
        datetime.timedelta(seconds=8),
    )

    def build_report() -> dict[str, Any]:
        result = f"Background report about {topic} is ready."
        reports[report_id] = {
            "id": report_id,
            "topic": topic,
            "status": "done",
            "result": result,
        }
        return reports[report_id]

    return await ctx.step.run("build-report", build_report)


app = FastAPI(
    title="A3 Background Job API",
    version="0.3.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/reports", status_code=202)
async def create_report(payload: ReportRequest) -> dict[str, str]:
    report_id = uuid.uuid4().hex
    reports[report_id] = {
        "id": report_id,
        "topic": payload.topic,
        "status": "pending",
    }

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": payload.topic,
            },
        )
    )

    return {"id": report_id, "status": "pending"}


@app.get("/reports/{report_id}")
def get_report(report_id: str) -> dict[str, Any]:
    report = reports.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello, make_report],
)