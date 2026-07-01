"""JSON serialization utilities."""

from __future__ import annotations

import json
from typing import Any


def dumps(data: Any, *, indent: int | None = None) -> str:
    """Serialize data to a JSON string.

    Args:
        data: Object to serialize.
        indent: Optional indentation for pretty printing.

    Returns:
        JSON string representation.
    """
    return json.dumps(data, default=str, indent=indent)


def loads(raw: str) -> Any:
    """Deserialize a JSON string.

    Args:
        raw: JSON string to parse.

    Returns:
        Parsed Python object.
    """
    return json.loads(raw)
