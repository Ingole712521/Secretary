"""Tool platform exception hierarchy."""

from __future__ import annotations

from app.exceptions.tool import ToolException


class ToolPlatformError(ToolException):
    """Base exception for the tool platform subsystem."""

    def __init__(
        self,
        message: str,
        *,
        tool_id: str | None = None,
        code: str = "TOOL_PLATFORM_ERROR",
    ) -> None:
        """Initialize a tool platform error.

        Args:
            message: Human-readable error description.
            tool_id: Optional tool identifier.
            code: Machine-readable error code.
        """
        super().__init__(message, tool_name=tool_id, code=code)
        self.tool_id = tool_id


class ToolNotFoundError(ToolPlatformError):
    """Raised when a tool ID is not registered."""

    def __init__(self, tool_id: str) -> None:
        """Initialize with missing tool ID.

        Args:
            tool_id: Tool identifier that was not found.
        """
        super().__init__(
            f"Tool not found: {tool_id}",
            tool_id=tool_id,
            code="TOOL_NOT_FOUND",
        )


class ToolRegistrationError(ToolPlatformError):
    """Raised when tool registration fails."""

    def __init__(self, message: str, *, tool_id: str | None = None) -> None:
        """Initialize a registration error.

        Args:
            message: Description of the registration failure.
            tool_id: Optional tool identifier.
        """
        super().__init__(message, tool_id=tool_id, code="TOOL_REGISTRATION_ERROR")


class ToolValidationError(ToolPlatformError):
    """Raised when tool parameter or security validation fails."""

    def __init__(self, message: str, *, tool_id: str | None = None) -> None:
        """Initialize a validation error.

        Args:
            message: Description of the validation failure.
            tool_id: Optional tool identifier.
        """
        super().__init__(message, tool_id=tool_id, code="TOOL_VALIDATION_ERROR")


class ToolPermissionDeniedError(ToolPlatformError):
    """Raised when the caller lacks required permissions."""

    def __init__(self, tool_id: str, required: list[str]) -> None:
        """Initialize a permission denied error.

        Args:
            tool_id: Tool identifier.
            required: Required permission levels.
        """
        perms = ", ".join(required)
        super().__init__(
            f"Permission denied for tool '{tool_id}'. Required: {perms}",
            tool_id=tool_id,
            code="TOOL_PERMISSION_DENIED",
        )
        self.required_permissions = required


class ToolSecurityError(ToolPlatformError):
    """Raised when a tool violates security policy."""

    def __init__(self, message: str, *, tool_id: str | None = None) -> None:
        """Initialize a security policy error.

        Args:
            message: Description of the policy violation.
            tool_id: Optional tool identifier.
        """
        super().__init__(message, tool_id=tool_id, code="TOOL_SECURITY_ERROR")


class ToolExecutionError(ToolPlatformError):
    """Raised when tool execution fails at runtime."""

    def __init__(self, message: str, *, tool_id: str | None = None) -> None:
        """Initialize an execution error.

        Args:
            message: Description of the execution failure.
            tool_id: Optional tool identifier.
        """
        super().__init__(message, tool_id=tool_id, code="TOOL_EXECUTION_ERROR")


class ToolConfirmationRequiredError(ToolPlatformError):
    """Raised when execution requires human confirmation."""

    def __init__(self, tool_id: str) -> None:
        """Initialize a confirmation required error.

        Args:
            tool_id: Tool awaiting confirmation.
        """
        super().__init__(
            f"Human confirmation required for tool: {tool_id}",
            tool_id=tool_id,
            code="TOOL_CONFIRMATION_REQUIRED",
        )
