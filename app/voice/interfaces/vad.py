"""Voice activity detection port."""

from __future__ import annotations

from typing import Protocol

from app.voice.schemas.models import VadResult


class VoiceActivityDetector(Protocol):
    """Port for detecting speech boundaries in audio."""

    @property
    def provider_name(self) -> str:
        """Return the VAD provider identifier."""
        ...

    async def health_check(self) -> bool:
        """Return True when VAD is available."""
        ...

    async def process_chunk(self, audio: bytes, *, sample_rate: int) -> VadResult:
        """Analyze an audio chunk for voice activity.

        Args:
            audio: PCM audio bytes.
            sample_rate: Sample rate of the audio.

        Returns:
            Voice activity analysis result.
        """
        ...

    async def reset(self) -> None:
        """Reset internal VAD state between utterances."""
        ...
