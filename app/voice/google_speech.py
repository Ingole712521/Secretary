"""High-accuracy speech-to-text via Google's free web speech endpoint.

Transcribes a recorded WAV file using the ``SpeechRecognition`` library's
``recognize_google`` backend. This needs an internet connection but no API
key and no native audio dependencies (audio capture is handled elsewhere).
"""

from __future__ import annotations

from pathlib import Path

import speech_recognition as sr


class GoogleSpeechError(RuntimeError):
    """Raised when transcription cannot reach or use the Google endpoint."""


class GoogleSpeechRecognizer:
    """Transcribe recorded audio files with Google's free speech API.

    Attributes:
        _recognizer: Underlying ``SpeechRecognition`` recognizer.
        _language: BCP-47 language tag used for recognition (e.g. en-US).
    """

    def __init__(self, *, language: str = "en-US") -> None:
        """Initialize the recognizer.

        Args:
            language: Recognition language tag, e.g. ``en-US`` or ``en-IN``.
        """
        self._recognizer = sr.Recognizer()
        self._language = language

    def transcribe(self, wav_path: Path) -> str:
        """Transcribe a WAV file to text.

        Args:
            wav_path: Path to a PCM WAV file containing a single utterance.

        Returns:
            Recognized text, or an empty string when nothing was understood.

        Raises:
            GoogleSpeechError: When the endpoint is unreachable or the audio
                file cannot be read (e.g. no internet connection).
        """
        try:
            with sr.AudioFile(str(wav_path)) as source:
                audio = self._recognizer.record(source)
        except (OSError, ValueError) as exc:
            msg = f"Could not read audio file: {exc}"
            raise GoogleSpeechError(msg) from exc

        try:
            result = self._recognizer.recognize_google(
                audio,
                language=self._language,
            )
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            msg = f"Google speech request failed: {exc}"
            raise GoogleSpeechError(msg) from exc

        return str(result).strip()
