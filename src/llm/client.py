from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from openai import APIStatusError, APITimeoutError, OpenAI

PROMPT_VERSION = "book-enrich-v1"
PROMPT_PATH = Path("prompts/book-enrich-v1.md")
CLIENT_TIMEOUT_SECONDS = 30.0
MAX_TRANSIENT_RETRIES = 3


class LLMTimeoutError(Exception):
    pass


class LLMProviderError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def create_client() -> OpenAI:
    # SDK retries are deliberately disabled so our retry policy is the only one.
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=CLIENT_TIMEOUT_SECONDS,
        max_retries=0,
    )


def _record_message(*, title: str, description: str) -> str:
    return json.dumps(
        {
            "source": "scraped_book_record",
            "title": title,
            "description": description,
        },
        ensure_ascii=False,
    )


def _emit_log(event: str, **fields: Any) -> None:
    record = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    print(json.dumps(record, ensure_ascii=False, sort_keys=True), flush=True)


def _retry_after_seconds(exc: APIStatusError) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)

    if not headers:
        return None

    value = headers.get("retry-after")
    if not value:
        return None

    value = value.strip()

    try:
        return max(0.0, float(value))
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(
            0.0,
            (retry_at - datetime.now(timezone.utc)).total_seconds(),
        )
    except (TypeError, ValueError, OverflowError):
        return None


def _backoff_seconds(retry_number: int) -> float:
    # retry_number is 1, 2, 3 -> about 1s, 2s, 4s plus jitter.
    base = 2 ** (retry_number - 1)
    return base + random.uniform(0.0, 0.25)


def _is_retryable_status(status_code: int | None) -> bool:
    if status_code == 429:
        return True
    return status_code is not None and 500 <= status_code <= 599


def _sleep_before_retry(
    *,
    retry_number: int,
    retry_after: float | None,
    reason: str,
) -> None:
    delay = retry_after if retry_after is not None else _backoff_seconds(retry_number)

    _emit_log(
        "llm_retry_scheduled",
        prompt_version=PROMPT_VERSION,
        model=os.environ["LLM_MODEL"],
        retry_number=retry_number,
        delay_seconds=round(delay, 3),
        reason=reason,
    )
    time.sleep(delay)


def _call_model(
    *,
    messages: list[dict[str, str]],
    repair_count: int,
) -> str:
    client = create_client()
    model = os.environ["LLM_MODEL"]

    for attempt_index in range(MAX_TRANSIENT_RETRIES + 1):
        attempt_number = attempt_index + 1
        started = time.perf_counter()

        _emit_log(
            "llm_provider_attempt",
            prompt_version=PROMPT_VERSION,
            model=model,
            attempt=attempt_number,
            repair_count=repair_count,
        )

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
            )

            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            usage = response.usage

            input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            total_tokens = int(getattr(usage, "total_tokens", 0) or 0)

            # The required provider lane uses openrouter/free, so provider
            # charge for successful free-router requests is $0.
            provider_cost_usd = 0.0 if model == "openrouter/free" else None

            _emit_log(
                "llm_call",
                prompt_version=PROMPT_VERSION,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                duration_ms=duration_ms,
                repair_count=repair_count,
                retries_used=attempt_index,
                provider_cost_usd=provider_cost_usd,
            )

            return response.choices[0].message.content or ""

        except APITimeoutError as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)

            _emit_log(
                "llm_provider_error",
                prompt_version=PROMPT_VERSION,
                model=model,
                attempt=attempt_number,
                repair_count=repair_count,
                status_code=None,
                error_type="timeout",
                duration_ms=duration_ms,
            )

            if attempt_index >= MAX_TRANSIENT_RETRIES:
                raise LLMTimeoutError(
                    "LLM provider timed out after the configured retry limit."
                ) from exc

            _sleep_before_retry(
                retry_number=attempt_index + 1,
                retry_after=None,
                reason="timeout",
            )

        except APIStatusError as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            status_code = getattr(exc, "status_code", None)

            _emit_log(
                "llm_provider_error",
                prompt_version=PROMPT_VERSION,
                model=model,
                attempt=attempt_number,
                repair_count=repair_count,
                status_code=status_code,
                error_type="http_status",
                duration_ms=duration_ms,
            )

            if _is_retryable_status(status_code):
                if attempt_index >= MAX_TRANSIENT_RETRIES:
                    raise LLMProviderError(
                        f"LLM provider HTTP {status_code} after retry limit.",
                        status_code=status_code,
                    ) from exc

                _sleep_before_retry(
                    retry_number=attempt_index + 1,
                    retry_after=_retry_after_seconds(exc),
                    reason=f"http_{status_code}",
                )
                continue

            # 400, 401, 403 and every other non-transient HTTP error fail fast.
            raise LLMProviderError(
                f"LLM provider HTTP {status_code}; request was not retried.",
                status_code=status_code,
            ) from exc

        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)

            _emit_log(
                "llm_provider_error",
                prompt_version=PROMPT_VERSION,
                model=model,
                attempt=attempt_number,
                repair_count=repair_count,
                status_code=None,
                error_type=type(exc).__name__,
                duration_ms=duration_ms,
            )

            raise LLMProviderError(
                "LLM provider request failed with a non-retryable client error."
            ) from exc

    raise AssertionError("Unreachable retry state")


def complete_enrichment(*, title: str, description: str) -> str:
    return _call_model(
        messages=[
            {
                "role": "system",
                "content": load_system_prompt(),
            },
            {
                "role": "user",
                "content": _record_message(
                    title=title,
                    description=description,
                ),
            },
        ],
        repair_count=0,
    )


def repair_enrichment(
    *,
    title: str,
    description: str,
    broken_output: str,
    validation_error: str,
) -> str:
    repair_message = json.dumps(
        {
            "task": "repair_previous_answer",
            "original_record": {
                "title": title,
                "description": description,
            },
            "broken_output": broken_output,
            "validation_error": validation_error,
            "instruction": (
                "Your previous answer was rejected for this reason. "
                "Return only corrected JSON matching the schema."
            ),
        },
        ensure_ascii=False,
    )

    return _call_model(
        messages=[
            {
                "role": "system",
                "content": load_system_prompt(),
            },
            {
                "role": "user",
                "content": repair_message,
            },
        ],
        repair_count=1,
    )
