"""Manual voice activity detection provider."""

from __future__ import annotations

import time

from app.voice.schemas.models import VadResult


class ManualVoiceActivityDetector:
    """End-of-speech detection using silence timeout after speech starts."""

    def __init__(self, *, silence_timeout_ms: int = 800) -> None:
        """Initialize manual VAD with a silence timeout."""
        self._silence_timeout_ms = silence_timeout_ms
        self._speech_started = False
        self._last_speech_at: float | None = None

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "manual"

    async def health_check(self) -> bool:
        """Manual VAD is always available."""
        return True

    async def process_chunk(self, audio: bytes, *, sample_rate: int) -> VadResult:
        """Detect speech using simple energy thresholding."""
        _ = sample_rate
        energy = sum(abs(byte - 128) for byte in audio) / max(len(audio), 1)
        is_speech = energy > 2.0
        now = time.monotonic()

        if is_speech:
            self._speech_started = True
            self._last_speech_at = now
            return VadResult(is_speech=True, speech_probability=min(energy / 10.0, 1.0))

        if not self._speech_started or self._last_speech_at is None:
            return VadResult(is_speech=False, speech_probability=0.0)

        silence_ms = (now - self._last_speech_at) * 1000
        if silence_ms >= self._silence_timeout_ms:
            self._speech_started = False
            self._last_speech_at = None
            return VadResult(is_speech=False, speech_probability=0.0, speech_ended=True)

        return VadResult(is_speech=False, speech_probability=0.1)

    async def reset(self) -> None:
        """Reset VAD state."""
        self._speech_started = False
        self._last_speech_at = None
