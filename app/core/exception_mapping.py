"""Map domain exceptions to HTTP status codes."""

from __future__ import annotations

from app.exceptions import (
    AuthenticationException,
    ConfigurationException,
    JarvisError,
    ToolException,
    ValidationException,
)
from app.tools.exceptions import ToolPermissionDeniedError, ToolValidationError

_STATUS_RESOLUTION_ORDER: list[tuple[type[JarvisError], int]] = [
    (ValidationException, 422),
    (ToolValidationError, 422),
    (ToolPermissionDeniedError, 403),
    (AuthenticationException, 401),
    (ConfigurationException, 500),
    (ToolException, 500),
]


def resolve_status_code(exc: JarvisError) -> int:
    """Resolve the HTTP status code for a domain exception.

    Walks the exception type hierarchy so subclasses receive the
    correct status code from their parent type.

    Args:
        exc: Domain exception instance.

    Returns:
        HTTP status code.
    """
    for exc_type, status_code in _STATUS_RESOLUTION_ORDER:
        if isinstance(exc, exc_type):
            return status_code
    return 500
