"""Memory subsystem exceptions."""

from __future__ import annotations

from app.exceptions.base import JarvisError


class MemoryError(JarvisError):
    """Base exception for memory subsystem errors."""

    def __init__(self, message: str, *, code: str = "MEMORY_ERROR") -> None:
        """Initialize a memory error.

        Args:
            message: Human-readable error description.
            code: Machine-readable error code.
        """
        super().__init__(message, code=code)


class MemoryNotFoundError(MemoryError):
    """Raised when a memory fact ID does not exist."""

    def __init__(self, memory_id: str) -> None:
        """Initialize with the missing memory ID.

        Args:
            memory_id: Identifier that was not found.
        """
        super().__init__(
            f"Memory not found: {memory_id}",
            code="MEMORY_NOT_FOUND",
        )
        self.memory_id = memory_id
