from __future__ import annotations

import json
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.llm.client import complete_enrichment
from src.llm.schema import EnrichRequest, EnrichResponse

router = APIRouter(tags=["Week 7 LLM enrichment"])


def _input_error(exc: ValidationError) -> JSONResponse:
    first = exc.errors()[0]
    location = first.get("loc") or ("request",)
    field = str(location[-1])
    message = first.get("msg", "invalid value")

    return JSONResponse(
        status_code=400,
        content={
            "error": f"Invalid field: {field}",
            "detail": message,
        },
    )


@router.post(
    "/enrich",
    summary="Enrich one scraped book record",
)
async def enrich_book(request: Request):
    try:
        raw = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid field: request",
                "detail": "Request body must be valid JSON",
            },
        )

    try:
        payload = EnrichRequest.model_validate(raw)
    except ValidationError as exc:
        return _input_error(exc)

    if os.getenv("LLM_STUB", "0") == "1":
        stub = EnrichResponse(
            category="fiction",
            summary=(
                f"{payload.title} is a fictional work represented by "
                "synthetic Stage 1 enrichment data."
            ),
            confidence=0.95,
            quality_flags=["none"],
            needs_review=False,
        )
        return stub.model_dump(mode="json")

    # Stage 2 deliberately exposes the raw answer for inspection.
    # Stage 3 replaces this with parse + schema validation + repair.
    raw_model_output = complete_enrichment(
        title=payload.title,
        description=payload.description,
    )

    return {
        "stage": 2,
        "prompt_version": "book-enrich-v1",
        "raw_model_output": raw_model_output,
    }
