"""Voice platform exception hierarchy."""

from __future__ import annotations

from app.exceptions.base import JarvisError


class VoiceError(JarvisError):
    """Base exception for voice subsystem errors."""

    def __init__(self, message: str, *, code: str = "VOICE_ERROR") -> None:
        """Initialize a voice error.

        Args:
            message: Human-readable error description.
            code: Machine-readable error code.
        """
        super().__init__(message, code=code)


class VoiceNotAvailableError(VoiceError):
    """Raised when voice services are disabled or misconfigured."""

    def __init__(self, message: str) -> None:
        """Initialize a voice unavailable error."""
        super().__init__(message, code="VOICE_NOT_AVAILABLE")


class VoiceLifecycleError(VoiceError):
    """Raised when an invalid lifecycle transition is attempted."""

    def __init__(self, message: str) -> None:
        """Initialize a lifecycle error."""
        super().__init__(message, code="VOICE_LIFECYCLE_ERROR")


class SpeechToTextError(VoiceError):
    """Raised when speech transcription fails."""

    def __init__(self, message: str) -> None:
        """Initialize an STT error."""
        super().__init__(message, code="SPEECH_TO_TEXT_ERROR")


class TextToSpeechError(VoiceError):
    """Raised when speech synthesis fails."""

    def __init__(self, message: str) -> None:
        """Initialize a TTS error."""
        super().__init__(message, code="TEXT_TO_SPEECH_ERROR")


class MicrophoneError(VoiceError):
    """Raised when microphone capture fails."""

    def __init__(self, message: str) -> None:
        """Initialize a microphone error."""
        super().__init__(message, code="MICROPHONE_ERROR")


class WakeWordError(VoiceError):
    """Raised when wake word detection fails."""

    def __init__(self, message: str) -> None:
        """Initialize a wake word error."""
        super().__init__(message, code="WAKE_WORD_ERROR")


class VoiceActivityDetectionError(VoiceError):
    """Raised when voice activity detection fails."""

    def __init__(self, message: str) -> None:
        """Initialize a VAD error."""
        super().__init__(message, code="VAD_ERROR")


class AudioOutputError(VoiceError):
    """Raised when audio playback fails."""

    def __init__(self, message: str) -> None:
        """Initialize an audio output error."""
        super().__init__(message, code="AUDIO_OUTPUT_ERROR")
