"""Environment variable utilities."""

from __future__ import annotations

import os


def get_env(name: str, default: str | None = None) -> str | None:
    """Read an environment variable.

    Args:
        name: Variable name.
        default: Value returned when the variable is unset.

    Returns:
        Environment variable value or default.
    """
    return os.environ.get(name, default)


def is_truthy(value: str | None) -> bool:
    """Return True when a string represents a truthy flag.

    Args:
        value: String value from an environment variable.

    Returns:
        True for common truthy strings (``1``, ``true``, ``yes``, ``on``).
    """
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}
