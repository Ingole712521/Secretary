"""Tool execution result models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.tools.schemas.enums import ToolResultStatus
from app.utils.date import utc_timestamp_iso


class ToolResult(BaseModel):
    """Normalized result from a tool execution.

    Attributes:
        status: Outcome status (success, failure, warning, retry, cancelled).
        output: Structured output data on success or partial success.
        error: Error message on failure.
        message: Human-readable result summary.
        retry_after_ms: Suggested retry delay for RETRY status.
        metadata: Additional result metadata.
        timestamp: ISO timestamp of result creation.
    """

    status: ToolResultStatus
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    message: str = ""
    retry_after_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=utc_timestamp_iso)

    @classmethod
    def success(
        cls,
        output: dict[str, Any] | None = None,
        *,
        message: str = "Tool executed successfully",
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create a success result.

        Args:
            output: Tool output data.
            message: Human-readable summary.
            metadata: Optional metadata.

        Returns:
            Success ``ToolResult``.
        """
        return cls(
            status=ToolResultStatus.SUCCESS,
            output=output or {},
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        error: str,
        *,
        message: str = "Tool execution failed",
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create a failure result.

        Args:
            error: Error description.
            message: Human-readable summary.
            metadata: Optional metadata.

        Returns:
            Failure ``ToolResult``.
        """
        return cls(
            status=ToolResultStatus.FAILURE,
            error=error,
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def warning(
        cls,
        output: dict[str, Any] | None = None,
        *,
        message: str = "Tool completed with warnings",
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create a warning result.

        Args:
            output: Partial output data.
            message: Human-readable summary.
            metadata: Optional metadata.

        Returns:
            Warning ``ToolResult``.
        """
        return cls(
            status=ToolResultStatus.WARNING,
            output=output or {},
            message=message,
            metadata=metadata or {},
        )

    @classmethod
    def retry(
        cls,
        *,
        message: str = "Tool execution should be retried",
        retry_after_ms: int = 1000,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create a retry result.

        Args:
            message: Human-readable summary.
            retry_after_ms: Suggested delay before retry.
            metadata: Optional metadata.

        Returns:
            Retry ``ToolResult``.
        """
        return cls(
            status=ToolResultStatus.RETRY,
            message=message,
            retry_after_ms=retry_after_ms,
            metadata=metadata or {},
        )

    @classmethod
    def cancelled(
        cls,
        *,
        message: str = "Tool execution was cancelled",
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Create a cancelled result.

        Args:
            message: Human-readable summary.
            metadata: Optional metadata.

        Returns:
            Cancelled ``ToolResult``.
        """
        return cls(
            status=ToolResultStatus.CANCELLED,
            message=message,
            metadata=metadata or {},
        )

    @property
    def is_success(self) -> bool:
        """Return True when status is success."""
        return self.status == ToolResultStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Return True when status is failure."""
        return self.status == ToolResultStatus.FAILURE
