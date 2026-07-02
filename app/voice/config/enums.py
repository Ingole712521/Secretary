"""Voice platform provider configuration enums."""

from __future__ import annotations

from enum import StrEnum


class VoiceSttProvider(StrEnum):
    """Speech-to-text provider identifiers."""

    FASTER_WHISPER = "faster_whisper"
    OPENAI = "openai"
    DEEPGRAM = "deepgram"
    GOOGLE = "google"
    AZURE = "azure"
    STUB = "stub"


class VoiceTtsProvider(StrEnum):
    """Text-to-speech provider identifiers."""

    PIPER = "piper"
    ELEVENLABS = "elevenlabs"
    AZURE = "azure"
    OPENAI = "openai"
    EDGE = "edge"
    STUB = "stub"


class VoiceVadProvider(StrEnum):
    """Voice activity detection provider identifiers."""

    SILERO = "silero"
    WEBRTC = "webrtc"
    MANUAL = "manual"
    STUB = "stub"


class VoiceWakeWordProvider(StrEnum):
    """Wake word provider identifiers."""

    OPENWAKEWORD = "openwakeword"
    PORCUPINE = "porcupine"
    CUSTOM = "custom"
    STUB = "stub"


class VoiceMicrophoneProvider(StrEnum):
    """Microphone provider identifiers."""

    SOUNDDEVICE = "sounddevice"
    STUB = "stub"


class VoiceAudioOutputProvider(StrEnum):
    """Audio output provider identifiers."""

    SOUNDDEVICE = "sounddevice"
    STUB = "stub"
