"""Configuration-related exceptions."""

from __future__ import annotations

from app.exceptions.base import JarvisError


class ConfigurationException(JarvisError):
    """Raised when configuration is missing or invalid."""

    def __init__(self, message: str, *, code: str = "CONFIGURATION_ERROR") -> None:
        """Initialize a configuration exception.

        Args:
            message: Description of the configuration problem.
            code: Machine-readable error code.
        """
        super().__init__(message, code=code)
