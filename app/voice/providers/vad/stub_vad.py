"""Stub voice activity detection provider."""

from __future__ import annotations

from app.voice.schemas.models import VadResult


class StubVoiceActivityDetector:
    """Configurable VAD stub for tests."""

    def __init__(
        self,
        *,
        is_speech: bool = True,
        speech_probability: float = 0.9,
        speech_ended: bool = False,
    ) -> None:
        """Initialize the stub VAD provider."""
        self._is_speech = is_speech
        self._speech_probability = speech_probability
        self._speech_ended = speech_ended

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "stub"

    async def health_check(self) -> bool:
        """Stub VAD is always healthy."""
        return True

    async def process_chunk(self, audio: bytes, *, sample_rate: int) -> VadResult:
        """Return configured VAD result."""
        _ = audio, sample_rate
        return VadResult(
            is_speech=self._is_speech,
            speech_probability=self._speech_probability,
            speech_ended=self._speech_ended,
        )

    async def reset(self) -> None:
        """Reset stub VAD state."""
        return
