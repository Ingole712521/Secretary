"""Tool platform schema enumerations."""

from __future__ import annotations

from enum import StrEnum


class ToolCategory(StrEnum):
    """High-level grouping for registered tools."""

    SYSTEM = "system"
    FILE = "file"
    NETWORK = "network"
    DEVELOPMENT = "development"
    AUTOMATION = "automation"
    CLOUD = "cloud"
    COMMUNICATION = "communication"
    CUSTOM = "custom"


class ToolPermissionLevel(StrEnum):
    """Standard permission levels required by tools."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    SYSTEM = "system"
    CUSTOM = "custom"


class ToolResultStatus(StrEnum):
    """Outcome status for tool execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    RETRY = "retry"
    CANCELLED = "cancelled"


class ConfirmationPolicy(StrEnum):
    """When human confirmation is required before execution."""

    NEVER = "never"
    ON_DANGEROUS = "on_dangerous"
    ON_WRITE = "on_write"
    ALWAYS = "always"
