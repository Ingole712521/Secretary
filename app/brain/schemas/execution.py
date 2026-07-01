"""Orchestrator input and output schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.brain.schemas.plan import ExecutionPlan


class ExecutionStatus(StrEnum):
    """High-level orchestration outcome status."""

    PLANNED = "planned"
    FAILED = "failed"
    REJECTED = "rejected"


class ExecutionRequest(BaseModel):
    """User request entering the Brain orchestrator.

    Attributes:
        user_input: Raw natural-language user input.
        conversation_id: Existing conversation to continue, if any.
        session_id: Optional session identifier.
        require_plan: Whether the orchestrator should produce a plan.
        metadata: Optional request metadata.
    """

    user_input: str
    conversation_id: str | None = None
    session_id: str | None = None
    require_plan: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Result returned by the Brain orchestrator.

    Attributes:
        status: Orchestration outcome status.
        plan: Generated execution plan, if planning was requested.
        conversation_id: Active or newly created conversation ID.
        message: Human-readable status message.
        metadata: Optional result metadata.
    """

    status: ExecutionStatus
    plan: ExecutionPlan | None = None
    conversation_id: str | None = None
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
