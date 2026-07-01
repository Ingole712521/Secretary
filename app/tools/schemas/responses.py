"""Tool execution response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.tools.results.models import ToolResult


class ToolExecutionResponse(BaseModel):
    """Structured response from the tool executor.

    Attributes:
        tool_id: Executed tool identifier.
        result: Normalized tool result.
        duration_ms: Execution duration in milliseconds.
        logs: Captured execution log lines.
        correlation_id: Request tracing identifier.
        validated: Whether validation passed before execution.
        permission_granted: Whether permission check passed.
    """

    tool_id: str
    result: ToolResult
    duration_ms: float = 0.0
    logs: list[str] = Field(default_factory=list)
    correlation_id: str | None = None
    validated: bool = False
    permission_granted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
