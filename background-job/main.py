from __future__ import annotations

import datetime
import logging

from fastapi import FastAPI
import inngest
import inngest.fast_api


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


app = FastAPI(
    title="A3 Background Job API",
    version="0.2.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello],
)