"""Text-to-speech port interface."""

from __future__ import annotations

from typing import Protocol

from app.voice.schemas.models import SynthesisResult


class TextToSpeech(Protocol):
    """Port for converting text to audio bytes."""

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        ...

    async def health_check(self) -> bool:
        """Return True when the provider is configured and reachable."""
        ...

    async def synthesize(self, text: str) -> SynthesisResult:
        """Synthesize speech audio from text.

        Args:
            text: Text to speak.

        Returns:
            Synthesis result with audio bytes.
        """
        ...
