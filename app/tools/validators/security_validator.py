"""Tool security validation."""

from __future__ import annotations

from typing import Any

from app.tools.schemas.enums import ToolPermissionLevel
from app.tools.security.policies import SecurityValidator


class SecurityPolicyValidator:
    """Validates tool execution against security policies."""

    def __init__(self, security: SecurityValidator) -> None:
        """Initialize with a security validator.

        Args:
            security: Security policy enforcer.
        """
        self._security = security

    def validate(
        self,
        tool_id: str,
        parameters: dict[str, Any],
        permissions: list[ToolPermissionLevel],
        *,
        confirmed: bool = False,
    ) -> None:
        """Run all security checks for a tool execution.

        Args:
            tool_id: Tool identifier.
            parameters: Validated parameters.
            permissions: Tool required permissions.
            confirmed: Whether user confirmation was obtained.

        Raises:
            ToolSecurityError: On policy violation.
            ToolConfirmationRequiredError: When confirmation is required.
        """
        self._security.check_tool_allowed(tool_id)
        self._security.check_dangerous_parameters(tool_id, parameters)
        self._security.check_confirmation_required(
            tool_id,
            parameters,
            confirmed=confirmed,
        )
        self._security.requires_confirmation(
            tool_id,
            permissions,
            confirmed=confirmed,
        )
