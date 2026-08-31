from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class BookCategory(str, Enum):
    fiction = "fiction"
    nonfiction = "nonfiction"
    poetry = "poetry"
    mystery_thriller = "mystery_thriller"
    romance = "romance"
    children_young_adult = "children_young_adult"
    other = "other"


class QualityFlag(str, Enum):
    encoding_issue = "encoding_issue"
    duplicate_text = "duplicate_text"
    too_vague = "too_vague"
    prompt_injection = "prompt_injection"
    none = "none"


class EnrichRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=3000)

    @field_validator("title", "description")
    @classmethod
    def strip_and_reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class EnrichResponse(BaseModel):
    category: BookCategory
    summary: str = Field(min_length=1, max_length=240)
    confidence: float = Field(ge=0.0, le=1.0)
    quality_flags: list[QualityFlag] = Field(min_length=1, max_length=5)
    needs_review: bool

    @model_validator(mode="after")
    def validate_quality_flags(self):
        if QualityFlag.none in self.quality_flags and len(self.quality_flags) != 1:
            raise ValueError("'none' cannot be combined with other quality flags")
        return self
