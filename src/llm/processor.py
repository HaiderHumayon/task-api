from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from src.llm.client import PROMPT_VERSION, complete_enrichment, repair_enrichment
from src.llm.schema import EnrichRequest, EnrichResponse

QUARANTINE_PATH = Path("logs/quarantine.jsonl")


class ModelOutputRejected(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _extract_json_object(raw: str) -> dict:
    text = raw.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    decoder = json.JSONDecoder()

    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue

        if isinstance(value, dict):
            return value

    raise ValueError("Model output did not contain a valid JSON object")


def _validate_output(raw: str) -> EnrichResponse:
    try:
        obj = _extract_json_object(raw)
        return EnrichResponse.model_validate(obj)
    except (ValueError, ValidationError) as exc:
        raise ValueError(str(exc)) from exc


def _quarantine(
    *,
    payload: EnrichRequest,
    first_output: str,
    second_output: str,
    error: str,
) -> None:
    QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": PROMPT_VERSION,
        "input": payload.model_dump(),
        "first_model_output": first_output,
        "second_model_output": second_output,
        "error": error,
    }

    with QUARANTINE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def enrich_with_validation(payload: EnrichRequest) -> EnrichResponse:
    first_output = complete_enrichment(
        title=payload.title,
        description=payload.description,
    )

    try:
        return _validate_output(first_output)
    except ValueError as first_error:
        repair_output = repair_enrichment(
            title=payload.title,
            description=payload.description,
            broken_output=first_output,
            validation_error=str(first_error),
        )

        try:
            return _validate_output(repair_output)
        except ValueError as second_error:
            _quarantine(
                payload=payload,
                first_output=first_output,
                second_output=repair_output,
                error=str(second_error),
            )
            raise ModelOutputRejected(
                "The model could not produce schema-valid JSON after one repair retry."
            ) from second_error
