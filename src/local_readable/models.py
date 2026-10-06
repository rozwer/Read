from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


JobState = Literal["queued", "running", "completed", "failed"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GlossaryEntry(BaseModel):
    source: str = Field(min_length=1, max_length=200)
    target: str = Field(min_length=1, max_length=200)


class JobRecord(BaseModel):
    id: str
    filename: str
    state: JobState = "queued"
    model: str
    source_language: str = "en"
    target_language: str = "ja"
    glossary: list[GlossaryEntry] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    progress: int = 0
    message: str = "待機中"
    source_pages: int | None = None
    translated_pages: int | None = None
    page_count_matches: bool | None = None
    source_url: str | None = None
    translated_url: str | None = None
    bilingual_url: str | None = None
    error: str | None = None
