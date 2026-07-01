"""Tool permission validation."""

from __future__ import annotations

from app.tools.exceptions import ToolPermissionDeniedError
from app.tools.permissions.checker import PermissionChecker, PermissionGrant
from app.tools.schemas.enums import ToolPermissionLevel


class PermissionValidator:
    """Validates caller permissions against tool requirements."""

    def __init__(self, checker: PermissionChecker | None = None) -> None:
        """Initialize with an optional permission checker.

        Args:
            checker: Permission checker instance. Uses default if omitted.
        """
        self._checker = checker or PermissionChecker()

    def validate(
        self,
        tool_id: str,
        required: list[ToolPermissionLevel],
        caller_permissions: list[ToolPermissionLevel],
        *,
        custom_required: list[str] | None = None,
        custom_granted: list[str] | None = None,
    ) -> PermissionGrant:
        """Validate caller permissions.

        Args:
            tool_id: Tool identifier.
            required: Permissions required by the tool.
            caller_permissions: Permissions held by the caller.
            custom_required: Optional custom permissions required.
            custom_granted: Optional custom permissions granted.

        Returns:
            Validated permission grant.

        Raises:
            ToolPermissionDeniedError: If permissions are insufficient.
        """
        grant = PermissionGrant(
            levels=caller_permissions,
            custom=custom_granted or [],
        )
        if not self._checker.check(required, grant, custom_required=custom_required):
            missing = self._checker.missing_permissions(required, grant)
            raise ToolPermissionDeniedError(tool_id, missing)
        return grant
