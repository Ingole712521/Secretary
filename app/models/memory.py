"""Memory API request and response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    """Request payload for storing a memory fact.

    Attributes:
        content: Fact text to remember.
        category: Optional category label.
        tags: Optional search tags.
        source: Optional source identifier.
    """

    content: str = Field(..., min_length=1, max_length=8_000)
    category: str | None = Field(default=None, max_length=128)
    tags: list[str] = Field(default_factory=list, max_length=32)
    source: str = Field(default="api", max_length=64)


class MemoryFactResponse(BaseModel):
    """Response payload for a stored memory fact."""

    id: str
    content: str
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: str
    created_at: datetime
    updated_at: datetime


class MemorySearchResultItem(BaseModel):
    """A single memory search hit."""

    id: str
    content: str
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    score: float
    updated_at: datetime


class MemorySearchResponse(BaseModel):
    """Response payload for memory search."""

    query: str
    results: list[MemorySearchResultItem] = Field(default_factory=list)
