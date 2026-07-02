"""Silero voice activity detection provider."""

from __future__ import annotations

import asyncio
import logging
import struct

from app.constants import LOGGER_ROOT
from app.voice.exceptions import VoiceActivityDetectionError
from app.voice.schemas.models import VadResult

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.vad.silero")


class SileroVoiceActivityDetector:
    """Silero VAD provider with automatic end-of-speech detection."""

    def __init__(self, *, silence_timeout_ms: int = 800) -> None:
        """Initialize Silero VAD."""
        self._silence_timeout_ms = silence_timeout_ms
        self._model: object | None = None
        self._speech_started = False
        self._last_speech_at: float | None = None

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "silero"

    async def health_check(self) -> bool:
        """Return True when torch and Silero VAD are importable."""
        try:
            import torch  # noqa: F401
        except ImportError:
            return False
        return True

    async def process_chunk(self, audio: bytes, *, sample_rate: int) -> VadResult:
        """Analyze an audio chunk with Silero VAD."""
        if not audio:
            return VadResult(is_speech=False, speech_probability=0.0)

        try:
            probability = await asyncio.to_thread(
                self._predict_probability,
                audio,
                sample_rate=sample_rate,
            )
        except ImportError as exc:
            raise VoiceActivityDetectionError(
                "torch is required for Silero VAD",
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise VoiceActivityDetectionError(f"Silero VAD failed: {exc}") from exc

        is_speech = probability >= 0.5
        if is_speech:
            self._speech_started = True
            self._last_speech_at = asyncio.get_running_loop().time()
            return VadResult(is_speech=True, speech_probability=probability)

        if self._speech_started and self._last_speech_at is not None:
            loop_time = asyncio.get_running_loop().time()
            silence_ms = (loop_time - self._last_speech_at) * 1000
            if silence_ms >= self._silence_timeout_ms:
                self._speech_started = False
                self._last_speech_at = None
                return VadResult(
                    is_speech=False,
                    speech_probability=probability,
                    speech_ended=True,
                )

        return VadResult(is_speech=False, speech_probability=probability)

    async def reset(self) -> None:
        """Reset VAD state."""
        self._speech_started = False
        self._last_speech_at = None

    def _get_model(self) -> object:
        """Load Silero VAD model from torch hub."""
        if self._model is not None:
            return self._model
        import torch

        model, _utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
        self._model = model
        return self._model

    def _predict_probability(self, audio: bytes, *, sample_rate: int) -> float:
        """Synchronously predict speech probability."""
        import torch

        model = self._get_model()
        sample_count = len(audio) // 2
        samples = struct.unpack(f"<{sample_count}h", audio)
        tensor = torch.tensor(samples, dtype=torch.float32) / 32768.0
        if sample_rate != 16000:
            ratio = 16000 / sample_rate
            indices = torch.linspace(0, len(tensor) - 1, int(len(tensor) * ratio))
            tensor = tensor[indices.long()]
        with torch.no_grad():
            probability = model(tensor, 16000).item()  # type: ignore[operator]
        return float(probability)
