"""Voice interaction subsystem for Jarvis OS."""

from app.voice.factory import build_speech_to_text, build_text_to_speech

__all__ = ["build_speech_to_text", "build_text_to_speech"]
