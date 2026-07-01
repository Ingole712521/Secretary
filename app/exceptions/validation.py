"""Validation-related exceptions."""

from __future__ import annotations

from app.exceptions.base import JarvisError


class ValidationException(JarvisError):
    """Raised when input validation fails."""

    def __init__(self, message: str, *, code: str = "VALIDATION_ERROR") -> None:
        """Initialize a validation exception.

        Args:
            message: Description of the validation failure.
            code: Machine-readable error code.
        """
        super().__init__(message, code=code)
