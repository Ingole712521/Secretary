"""Speech-to-text port interface."""

from __future__ import annotations

from typing import Protocol

from app.voice.schemas.models import TranscriptionResult


class SpeechToText(Protocol):
    """Port for converting audio bytes to text."""

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        ...

    async def health_check(self) -> bool:
        """Return True when the provider is configured and reachable."""
        ...

    async def transcribe(
        self,
        audio: bytes,
        *,
        audio_format: str = "webm",
        language: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe audio bytes to text.

        Args:
            audio: Raw audio data.
            audio_format: Audio format hint (webm, wav, mp3).
            language: Optional language code.

        Returns:
            Transcription result with text.
        """
        ...
