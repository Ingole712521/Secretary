"""Voice platform configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.config.settings import Settings


@dataclass(frozen=True, slots=True)
class VoicePlatformConfig:
    """Resolved voice platform configuration snapshot.

    Attributes:
        enabled: Whether voice is enabled.
        wake_word: Wake phrase to detect.
        language: Default speech language code.
        silence_timeout_ms: End-of-speech silence threshold.
        microphone_device: Optional input device index or name.
        speaker_device: Optional output device index or name.
        stt_provider: STT provider key.
        tts_provider: TTS provider key.
        vad_provider: VAD provider key.
        wakeword_provider: Wake word provider key.
        microphone_provider: Microphone provider key.
        audio_output_provider: Audio output provider key.
        whisper_model: Faster Whisper / Whisper model name.
        whisper_device: Inference device (cpu, cuda).
        whisper_compute_type: Faster Whisper compute type.
        piper_voice: Piper voice model path or name.
        piper_speed: Piper speech speed multiplier.
        piper_pitch: Piper pitch multiplier.
        piper_volume: Piper volume multiplier.
        sample_rate: Audio capture sample rate.
    """

    enabled: bool
    wake_word: str
    language: str
    silence_timeout_ms: int
    microphone_device: str | None
    speaker_device: str | None
    stt_provider: str
    tts_provider: str
    vad_provider: str
    wakeword_provider: str
    microphone_provider: str
    audio_output_provider: str
    whisper_model: str
    whisper_device: str
    whisper_compute_type: str
    piper_voice: str
    piper_speed: float
    piper_pitch: float
    piper_volume: float
    sample_rate: int


def build_voice_platform_config(settings: Settings) -> VoicePlatformConfig:
    """Build a voice platform config object from application settings.

    Args:
        settings: Application settings.

    Returns:
        Resolved voice platform configuration.
    """
    return VoicePlatformConfig(
        enabled=settings.voice_enabled,
        wake_word=settings.voice_wake_word,
        language=settings.voice_language,
        silence_timeout_ms=settings.voice_silence_timeout_ms,
        microphone_device=settings.voice_microphone_device,
        speaker_device=settings.voice_speaker_device,
        stt_provider=settings.voice_stt_provider,
        tts_provider=settings.voice_tts_provider,
        vad_provider=settings.voice_vad_provider,
        wakeword_provider=settings.voice_wakeword_provider,
        microphone_provider=settings.voice_microphone_provider,
        audio_output_provider=settings.voice_audio_output_provider,
        whisper_model=settings.voice_whisper_model,
        whisper_device=settings.voice_whisper_device,
        whisper_compute_type=settings.voice_whisper_compute_type,
        piper_voice=settings.voice_piper_voice,
        piper_speed=settings.voice_piper_speed,
        piper_pitch=settings.voice_piper_pitch,
        piper_volume=settings.voice_piper_volume,
        sample_rate=settings.voice_sample_rate,
    )
