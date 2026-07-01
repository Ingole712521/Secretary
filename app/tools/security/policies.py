"""Tool security policies and sandbox interface."""

from __future__ import annotations

import re
from typing import Protocol

from pydantic import BaseModel, Field

from app.tools.exceptions import ToolConfirmationRequiredError, ToolSecurityError
from app.tools.schemas.enums import ConfirmationPolicy, ToolPermissionLevel


class ToolSecurityPolicy(BaseModel):
    """Security policy governing tool execution.

    Attributes:
        whitelist: Allowed tool IDs. Empty means all registered tools allowed.
        blacklist: Blocked tool IDs.
        confirmation_policy: When human confirmation is required.
        dangerous_patterns: Regex patterns blocked in string parameters.
        require_sandbox: Whether tools must run inside a sandbox.
    """

    whitelist: list[str] = Field(default_factory=list)
    blacklist: list[str] = Field(default_factory=list)
    confirmation_policy: ConfirmationPolicy = ConfirmationPolicy.ON_DANGEROUS
    dangerous_patterns: list[str] = Field(
        default_factory=lambda: [
            r"rm\s+-rf",
            r"sudo\s+",
            r"format\s+c:",
            r"DROP\s+TABLE",
            r";\s*--",
        ],
    )
    require_sandbox: bool = False


class Sandbox(Protocol):
    """Port for sandboxed tool execution environments.

    Future implementations may use containers, subprocess isolation,
    or OS-level sandboxes. Sprint 3 defines the interface only.
    """

    async def prepare(self, tool_id: str) -> None:
        """Prepare the sandbox for a tool execution.

        Args:
            tool_id: Tool to prepare for.
        """
        ...

    async def execute_isolated(self, tool_id: str, params: dict[str, object]) -> object:
        """Execute within the sandbox (future use).

        Args:
            tool_id: Tool identifier.
            params: Execution parameters.

        Returns:
            Sandbox execution result.
        """
        ...

    async def cleanup(self, tool_id: str) -> None:
        """Clean up sandbox resources.

        Args:
            tool_id: Tool that was executed.
        """
        ...


class SecurityValidator:
    """Enforces whitelist, blacklist, confirmation, and dangerous command policies."""

    def __init__(self, policy: ToolSecurityPolicy) -> None:
        """Initialize with a security policy.

        Args:
            policy: Security policy configuration.
        """
        self._policy = policy
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in policy.dangerous_patterns
        ]

    @property
    def policy(self) -> ToolSecurityPolicy:
        """Return the active security policy."""
        return self._policy

    def check_tool_allowed(self, tool_id: str) -> None:
        """Verify a tool is allowed by whitelist/blacklist policy.

        Args:
            tool_id: Tool identifier.

        Raises:
            ToolSecurityError: If the tool is blocked.
        """
        if tool_id in self._policy.blacklist:
            msg = f"Tool '{tool_id}' is blacklisted"
            raise ToolSecurityError(msg, tool_id=tool_id)

        if self._policy.whitelist and tool_id not in self._policy.whitelist:
            msg = f"Tool '{tool_id}' is not in the whitelist"
            raise ToolSecurityError(msg, tool_id=tool_id)

    def check_dangerous_parameters(
        self,
        tool_id: str,
        parameters: dict[str, object],
    ) -> bool:
        """Scan parameters for dangerous patterns.

        Args:
            tool_id: Tool identifier (for error context).
            parameters: Tool input parameters.

        Returns:
            True if dangerous content was detected.

        Raises:
            ToolSecurityError: When a dangerous pattern is found.
        """
        for value in parameters.values():
            if not isinstance(value, str):
                continue
            for pattern in self._compiled_patterns:
                if pattern.search(value):
                    msg = f"Dangerous pattern detected in tool '{tool_id}' parameters"
                    raise ToolSecurityError(msg, tool_id=tool_id)
        return False

    def requires_confirmation(
        self,
        tool_id: str,
        permissions: list[ToolPermissionLevel],
        *,
        confirmed: bool = False,
    ) -> None:
        """Enforce confirmation policy before execution.

        Args:
            tool_id: Tool identifier.
            permissions: Tool required permissions.
            confirmed: Whether the user has already confirmed.

        Raises:
            ToolConfirmationRequiredError: When confirmation is required but missing.
        """
        if confirmed:
            return

        policy = self._policy.confirmation_policy
        needs_confirmation = (
            policy == ConfirmationPolicy.ALWAYS
            or (
                policy == ConfirmationPolicy.ON_WRITE
                and ToolPermissionLevel.WRITE in permissions
            )
            or (
                policy == ConfirmationPolicy.ON_DANGEROUS
                and (
                    ToolPermissionLevel.SYSTEM in permissions
                    or ToolPermissionLevel.ADMIN in permissions
                )
            )
        )

        if needs_confirmation:
            raise ToolConfirmationRequiredError(tool_id)
