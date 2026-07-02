"""Piper local text-to-speech provider."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from app.constants import LOGGER_ROOT
from app.voice.exceptions import TextToSpeechError
from app.voice.schemas.models import SynthesisOptions, SynthesisResult
from app.voice.utils.audio import pcm_to_wav

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.tts.piper")


class PiperTextToSpeech:
    """Local Piper TTS provider with configurable voice and prosody."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the Piper TTS provider."""
        self._settings = settings
        self._voice: object | None = None

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "piper"

    async def health_check(self) -> bool:
        """Return True when Piper voice assets are available."""
        exists = await asyncio.to_thread(
            os.path.exists,
            self._settings.voice_piper_voice,
        )
        if exists:
            return True
        try:
            from piper import PiperVoice  # noqa: F401
        except ImportError:
            return False
        return True

    async def synthesize(
        self,
        text: str,
        *,
        options: SynthesisOptions | None = None,
    ) -> SynthesisResult:
        """Synthesize speech using Piper."""
        if not text.strip():
            raise TextToSpeechError("Cannot synthesize empty text")

        opts = options or SynthesisOptions(
            voice=self._settings.voice_piper_voice,
            speed=self._settings.voice_piper_speed,
            pitch=self._settings.voice_piper_pitch,
            volume=self._settings.voice_piper_volume,
        )
        try:
            pcm, sample_rate = await asyncio.to_thread(
                self._synthesize_sync,
                text,
                opts,
            )
        except ImportError as exc:
            raise TextToSpeechError("piper-tts is not installed") from exc
        except Exception as exc:  # noqa: BLE001
            raise TextToSpeechError(f"Piper TTS failed: {exc}") from exc

        wav_audio = pcm_to_wav(pcm, sample_rate=sample_rate)
        logger.info("Piper TTS success | chars=%d bytes=%d", len(text), len(wav_audio))
        return SynthesisResult(
            audio=wav_audio,
            format="wav",
            provider=self.provider_name,
            sample_rate=sample_rate,
        )

    async def synthesize_stream(
        self,
        text: str,
        *,
        options: SynthesisOptions | None = None,
    ) -> AsyncIterator[bytes]:
        """Yield synthesized audio chunks."""
        result = await self.synthesize(text, options=options)
        yield result.audio

    def _get_voice(self) -> object:
        """Load and cache the Piper voice model."""
        if self._voice is not None:
            return self._voice
        try:
            from piper import PiperVoice
        except ImportError as exc:
            raise TextToSpeechError("piper-tts is not installed") from exc

        voice_path = self._settings.voice_piper_voice
        if not os.path.exists(voice_path):
            raise TextToSpeechError(f"Piper voice model not found: {voice_path}")
        self._voice = PiperVoice.load(voice_path)
        return self._voice

    def _synthesize_sync(
        self,
        text: str,
        options: SynthesisOptions,
    ) -> tuple[bytes, int]:
        """Synchronously synthesize PCM audio with Piper."""
        voice = self._get_voice()
        synthesizer = voice.synthesize(  # type: ignore[attr-defined]
            text,
            length_scale=1.0 / max(options.speed, 0.1),
            noise_scale=0.667,
            noise_w=0.8,
        )
        pcm = bytes(synthesizer.audio)
        sample_rate = int(getattr(voice.config, "sample_rate", 22050))  # type: ignore[attr-defined]
        return pcm, sample_rate
