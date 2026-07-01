"""Tool execution request schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.tools.schemas.enums import ToolPermissionLevel


class ToolExecutionRequest(BaseModel):
    """Request to execute a registered tool.

    Attributes:
        tool_id: Target tool identifier.
        parameters: Tool input parameters.
        correlation_id: Request tracing identifier.
        dry_run: When True, validate only without side effects.
        caller_permissions: Permissions granted to the caller.
        session_id: Optional session context.
        metadata: Optional execution metadata.
    """

    tool_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    dry_run: bool = False
    caller_permissions: list[ToolPermissionLevel] = Field(default_factory=list)
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
