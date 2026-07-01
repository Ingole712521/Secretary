"""Voice adapter factory."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from app.voice.adapters.edge_tts import EdgeTextToSpeech
from app.voice.adapters.openai_tts import OpenAiTts
from app.voice.adapters.openai_whisper import OpenAiWhisperStt
from app.voice.adapters.stub_stt import StubSpeechToText
from app.voice.adapters.stub_tts import StubTextToSpeech

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.voice.interfaces.speech_to_text import SpeechToText
    from app.voice.interfaces.text_to_speech import TextToSpeech


class VoiceSttProviderSetting(StrEnum):
    """Speech-to-text provider selection."""

    OPENAI = "openai"
    STUB = "stub"


class VoiceTtsProviderSetting(StrEnum):
    """Text-to-speech provider selection."""

    EDGE = "edge"
    OPENAI = "openai"
    STUB = "stub"


def build_speech_to_text(settings: Settings) -> SpeechToText:
    """Construct the configured STT adapter.

    Args:
        settings: Application settings.

    Returns:
        Speech-to-text adapter instance.
    """
    if settings.voice_stt_provider == VoiceSttProviderSetting.STUB.value:
        return StubSpeechToText()
    return OpenAiWhisperStt(settings)


def build_text_to_speech(settings: Settings) -> TextToSpeech:
    """Construct the configured TTS adapter.

    Args:
        settings: Application settings.

    Returns:
        Text-to-speech adapter instance.
    """
    if settings.voice_tts_provider == VoiceTtsProviderSetting.STUB.value:
        return StubTextToSpeech()
    if settings.voice_tts_provider == VoiceTtsProviderSetting.OPENAI.value:
        return OpenAiTts(settings)
    return EdgeTextToSpeech(settings)
