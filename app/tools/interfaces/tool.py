"""Tool interface contract for all executable tools."""

from __future__ import annotations

from typing import Any, Protocol

from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter


class Tool(Protocol):
    """Contract every tool implementation must satisfy.

    Tools are registered with the ``ToolRegistry`` and executed via
    the ``ToolExecutor``. Implementations must be async-safe.
    """

    @property
    def id(self) -> str:
        """Unique tool identifier."""
        ...

    @property
    def name(self) -> str:
        """Human-readable tool name."""
        ...

    @property
    def description(self) -> str:
        """Description of tool capabilities."""
        ...

    @property
    def category(self) -> ToolCategory:
        """Tool category for grouping."""
        ...

    @property
    def parameters(self) -> list[ToolParameter]:
        """Declared input parameters."""
        ...

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permission levels."""
        ...

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool with validated parameters.

        Args:
            params: Validated input parameters.

        Returns:
            Structured tool result.
        """
        ...

    async def validate(self, params: dict[str, Any]) -> ToolResult:
        """Validate parameters without executing side effects.

        Args:
            params: Input parameters to validate.

        Returns:
            Success result if valid; failure result with error details otherwise.
        """
        ...

    async def dry_run(self, params: dict[str, Any]) -> ToolResult:
        """Simulate execution without side effects.

        Args:
            params: Input parameters.

        Returns:
            Predicted execution result.
        """
        ...

    async def health(self) -> bool:
        """Report whether the tool is operational.

        Returns:
            True if the tool is healthy and ready.
        """
        ...
