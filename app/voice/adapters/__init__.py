"""Backward-compatible adapter re-exports."""

from app.voice.providers.stt.openai_whisper import OpenAiWhisperStt
from app.voice.providers.stt.stub_stt import StubSpeechToText
from app.voice.providers.tts.edge_tts import EdgeTextToSpeech
from app.voice.providers.tts.openai_tts import OpenAiTts
from app.voice.providers.tts.stub_tts import StubTextToSpeech

__all__ = [
    "EdgeTextToSpeech",
    "OpenAiTts",
    "OpenAiWhisperStt",
    "StubSpeechToText",
    "StubTextToSpeech",
]
