"""Base exception for all Jarvis OS errors."""

from __future__ import annotations


class JarvisError(Exception):
    """Base exception for all application errors.

    Attributes:
        message: Human-readable error description.
        code: Machine-readable error code for API responses.
    """

    def __init__(self, message: str, *, code: str = "INTERNAL_ERROR") -> None:
        """Initialize the base exception.

        Args:
            message: Human-readable error description.
            code: Machine-readable error code.
        """
        super().__init__(message)
        self.message = message
        self.code = code
