"""Composite tool validation orchestrator."""

from __future__ import annotations

from typing import Any

from app.tools.interfaces.tool import Tool
from app.tools.permissions.checker import PermissionGrant
from app.tools.schemas.enums import ToolPermissionLevel
from app.tools.validators.parameter_validator import ParameterValidator
from app.tools.validators.permission_validator import PermissionValidator
from app.tools.validators.security_validator import SecurityPolicyValidator


class ToolValidator:
    """Orchestrates parameter, permission, and security validation."""

    def __init__(
        self,
        parameter_validator: ParameterValidator,
        permission_validator: PermissionValidator,
        security_validator: SecurityPolicyValidator,
    ) -> None:
        """Initialize with validator dependencies.

        Args:
            parameter_validator: Parameter schema validator.
            permission_validator: Permission validator.
            security_validator: Security policy validator.
        """
        self._parameters = parameter_validator
        self._permissions = permission_validator
        self._security = security_validator

    def validate_execution(
        self,
        tool: Tool,
        parameters: dict[str, Any],
        caller_permissions: list[ToolPermissionLevel],
        *,
        confirmed: bool = False,
    ) -> tuple[dict[str, Any], PermissionGrant]:
        """Run full validation pipeline for a tool execution.

        Args:
            tool: Target tool instance.
            parameters: Raw input parameters.
            caller_permissions: Caller's permission levels.
            confirmed: Whether dangerous execution was confirmed.

        Returns:
            Tuple of validated parameters and permission grant.

        Raises:
            ToolValidationError: On parameter validation failure.
            ToolPermissionDeniedError: On permission failure.
            ToolSecurityError: On security policy violation.
        """
        validated = self._parameters.validate(
            tool.id,
            parameters,
            tool.parameters,
        )
        grant = self._permissions.validate(
            tool.id,
            tool.permissions,
            caller_permissions,
        )
        self._security.validate(
            tool.id,
            validated,
            tool.permissions,
            confirmed=confirmed,
        )
        return validated, grant
