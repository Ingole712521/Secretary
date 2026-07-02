"""Provider registry for future voice platform extensions."""

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


class VoiceProviderRegistry[T]:
    """Simple registry mapping provider keys to factory callables."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._providers: dict[str, T] = {}

    def register(self, key: str, provider: T) -> None:
        """Register a provider factory or instance."""
        self._providers[key] = provider

    def get(self, key: str) -> T:
        """Return a registered provider."""
        if key not in self._providers:
            msg = f"Voice provider not registered: {key}"
            raise KeyError(msg)
        return self._providers[key]

    def keys(self) -> list[str]:
        """Return registered provider keys."""
        return list(self._providers.keys())
