"""Desktop automation exceptions."""

from __future__ import annotations

from app.exceptions.tool import ToolException


class DesktopAutomationError(ToolException):
    """Raised when a desktop automation action fails."""

    def __init__(self, message: str) -> None:
        """Initialize a desktop automation error.

        Args:
            message: Human-readable error description.
        """
        super().__init__(message, code="DESKTOP_AUTOMATION_ERROR")
