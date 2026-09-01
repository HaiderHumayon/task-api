from __future__ import annotations

import json
import os
from pathlib import Path

from openai import OpenAI

PROMPT_VERSION = "book-enrich-v1"
PROMPT_PATH = Path("prompts/book-enrich-v1.md")


def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def create_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,
        max_retries=0,
    )


def complete_enrichment(*, title: str, description: str) -> str:
    system_prompt = load_system_prompt()

    user_record = json.dumps(
        {
            "source": "scraped_book_record",
            "title": title,
            "description": description,
        },
        ensure_ascii=False,
    )

    response = create_client().chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_record,
            },
        ],
        temperature=0,
    )

    return response.choices[0].message.content or ""
