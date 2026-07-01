"""Date and time utilities."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC datetime with timezone awareness.

    Returns:
        Current UTC datetime.
    """
    return datetime.now(UTC)


def utc_timestamp_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format.

    Returns:
        ISO 8601 formatted timestamp string.
    """
    return utc_now().isoformat()
