"""Common API response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Standard error detail payload."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    correlation_id: str | None = Field(
        default=None,
        description="Request correlation ID when available",
    )


class ErrorResponse(BaseModel):
    """Standard API error envelope."""

    error: ErrorDetail
