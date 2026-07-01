"""Tool permission models and checking."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.tools.schemas.enums import ToolPermissionLevel


class PermissionGrant(BaseModel):
    """Permissions granted to a caller for tool execution.

    Attributes:
        levels: Standard permission levels (read, write, execute, etc.).
        custom: Custom permission strings for specialized tools.
    """

    levels: list[ToolPermissionLevel] = Field(default_factory=list)
    custom: list[str] = Field(default_factory=list)

    def has_level(self, required: ToolPermissionLevel) -> bool:
        """Return True if the grant includes a permission level.

        Args:
            required: Required permission level.

        Returns:
            True if granted, including via ADMIN or SYSTEM supersets.
        """
        if required in self.levels:
            return True
        if ToolPermissionLevel.ADMIN in self.levels:
            return True
        if ToolPermissionLevel.SYSTEM in self.levels:
            return True
        return required == ToolPermissionLevel.CUSTOM

    def has_custom(self, permission: str) -> bool:
        """Return True if a custom permission is granted.

        Args:
            permission: Custom permission string.

        Returns:
            True if present in custom grants or caller has ADMIN/SYSTEM.
        """
        if permission in self.custom:
            return True
        return (
            ToolPermissionLevel.ADMIN in self.levels
            or ToolPermissionLevel.SYSTEM in self.levels
        )


class PermissionChecker:
    """Validates caller permissions against tool requirements."""

    def check(
        self,
        required: list[ToolPermissionLevel],
        granted: PermissionGrant,
        *,
        custom_required: list[str] | None = None,
    ) -> bool:
        """Return True when the caller has all required permissions.

        Args:
            required: Permission levels required by the tool.
            granted: Permissions held by the caller.
            custom_required: Optional custom permission strings.

        Returns:
            True if all requirements are satisfied.
        """
        for level in required:
            if level == ToolPermissionLevel.CUSTOM:
                continue
            if not granted.has_level(level):
                return False

        if custom_required:
            for custom in custom_required:
                if not granted.has_custom(custom):
                    return False

        return True

    def missing_permissions(
        self,
        required: list[ToolPermissionLevel],
        granted: PermissionGrant,
    ) -> list[str]:
        """Return a list of missing permission level names.

        Args:
            required: Required permission levels.
            granted: Granted permissions.

        Returns:
            Names of missing permission levels.
        """
        missing: list[str] = []
        for level in required:
            if level == ToolPermissionLevel.CUSTOM:
                continue
            if not granted.has_level(level):
                missing.append(level.value)
        return missing
