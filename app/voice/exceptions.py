"""Voice subsystem exceptions."""

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
        """Initialize a voice unavailable error.

        Args:
            message: Description of the configuration problem.
        """
        super().__init__(message, code="VOICE_NOT_AVAILABLE")


class SpeechToTextError(VoiceError):
    """Raised when speech transcription fails."""

    def __init__(self, message: str) -> None:
        """Initialize an STT error.

        Args:
            message: Description of the transcription failure.
        """
        super().__init__(message, code="SPEECH_TO_TEXT_ERROR")


class TextToSpeechError(VoiceError):
    """Raised when speech synthesis fails."""

    def __init__(self, message: str) -> None:
        """Initialize a TTS error.

        Args:
            message: Description of the synthesis failure.
        """
        super().__init__(message, code="TEXT_TO_SPEECH_ERROR")
