"""Voice platform exceptions."""

from app.voice.exceptions.errors import (
    AudioOutputError,
    MicrophoneError,
    SpeechToTextError,
    TextToSpeechError,
    VoiceActivityDetectionError,
    VoiceError,
    VoiceLifecycleError,
    VoiceNotAvailableError,
    WakeWordError,
)

__all__ = [
    "AudioOutputError",
    "MicrophoneError",
    "SpeechToTextError",
    "TextToSpeechError",
    "VoiceActivityDetectionError",
    "VoiceError",
    "VoiceLifecycleError",
    "VoiceNotAvailableError",
    "WakeWordError",
]
