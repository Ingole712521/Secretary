"""Tool execution exceptions (reserved for future tool framework)."""

from __future__ import annotations

from app.exceptions.base import JarvisError


class ToolException(JarvisError):
    """Raised when a tool operation fails.

    Reserved for the Phase 4 tool framework. Defined now so callers
    can depend on a stable exception type without future refactors.
    """

    def __init__(
        self,
        message: str,
        *,
        tool_name: str | None = None,
        code: str = "TOOL_ERROR",
    ) -> None:
        """Initialize a tool exception.

        Args:
            message: Description of the tool failure.
            tool_name: Optional name of the tool that failed.
            code: Machine-readable error code.
        """
        super().__init__(message, code=code)
        self.tool_name = tool_name
