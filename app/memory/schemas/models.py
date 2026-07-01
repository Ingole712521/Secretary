"""Memory domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.utils.date import utc_now


class MemoryFact(BaseModel):
    """A persistent fact stored in long-term memory.

    Attributes:
        id: Unique memory identifier.
        content: Fact text (e.g. ``User's name is Nehal``).
        category: Optional grouping (personal, preference, project).
        tags: Optional search tags.
        source: Origin of the fact (api, user, system).
        metadata: Arbitrary metadata.
        created_at: UTC creation timestamp.
        updated_at: UTC last-update timestamp.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(..., min_length=1, max_length=8_000)
    category: str | None = Field(default=None, max_length=128)
    tags: list[str] = Field(default_factory=list)
    source: str = Field(default="api", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def touch(self) -> None:
        """Update the last-modified timestamp."""
        self.updated_at = utc_now()


class MemorySearchResult(BaseModel):
    """A memory fact returned from search with relevance score.

    Attributes:
        fact: Matching memory fact.
        score: Relevance score (higher is better).
    """

    fact: MemoryFact
    score: float = Field(default=0.0, ge=0.0)
