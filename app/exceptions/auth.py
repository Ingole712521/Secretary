"""Authentication and authorization exceptions."""

from __future__ import annotations

from app.exceptions.base import JarvisError


class AuthenticationException(JarvisError):
    """Raised when authentication or authorization fails."""

    def __init__(self, message: str, *, code: str = "AUTHENTICATION_ERROR") -> None:
        """Initialize an authentication exception.

        Args:
            message: Description of the auth failure.
            code: Machine-readable error code.
        """
        super().__init__(message, code=code)
