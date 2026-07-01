"""Tool platform factory and dependency wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.tools.bootstrap import register_production_tools
from app.tools.executor.executor import ToolExecutor
from app.tools.permissions.checker import PermissionChecker
from app.tools.registry.registry import ToolRegistry
from app.tools.security.noop_sandbox import NoOpSandbox
from app.tools.security.policies import SecurityValidator, ToolSecurityPolicy
from app.tools.validators.parameter_validator import ParameterValidator
from app.tools.validators.permission_validator import PermissionValidator
from app.tools.validators.security_validator import SecurityPolicyValidator
from app.tools.validators.tool_validator import ToolValidator

if TYPE_CHECKING:
    from app.config.settings import Settings


@dataclass
class ToolPlatformContainer:
    """Holds all tool platform components for dependency injection.

    Attributes:
        registry: Tool registration and discovery.
        executor: Tool execution engine.
        validator: Composite validation pipeline.
        security: Security policy enforcer.
    """

    registry: ToolRegistry
    executor: ToolExecutor
    validator: ToolValidator
    security: SecurityValidator


def build_tool_platform(
    policy: ToolSecurityPolicy | None = None,
    settings: Settings | None = None,
) -> ToolPlatformContainer:
    """Construct the tool platform with default Sprint 3 components.

    Args:
        policy: Optional security policy override.
        settings: Optional settings for registering production tools.

    Returns:
        Wired ``ToolPlatformContainer``.
    """
    resolved_policy = policy or ToolSecurityPolicy()
    registry = ToolRegistry()
    security = SecurityValidator(resolved_policy)
    sandbox = NoOpSandbox() if resolved_policy.require_sandbox else None

    parameter_validator = ParameterValidator()
    permission_validator = PermissionValidator(PermissionChecker())
    security_validator = SecurityPolicyValidator(security)
    validator = ToolValidator(
        parameter_validator,
        permission_validator,
        security_validator,
    )
    executor = ToolExecutor(registry, validator, sandbox=sandbox)

    if settings is not None:
        register_production_tools(registry, settings)

    return ToolPlatformContainer(
        registry=registry,
        executor=executor,
        validator=validator,
        security=security,
    )
