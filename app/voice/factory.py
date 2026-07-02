"""Voice platform factory and dependency container."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.voice.audio.queue_player import QueueAudioPlayer
from app.voice.audio.stub_audio_output import StubAudioOutput
from app.voice.config.enums import (
    VoiceAudioOutputProvider,
    VoiceMicrophoneProvider,
    VoiceSttProvider,
    VoiceTtsProvider,
    VoiceVadProvider,
    VoiceWakeWordProvider,
)
from app.voice.conversation.controller import ConversationController
from app.voice.events import VoiceEventBus
from app.voice.manager.voice_manager import VoiceManager
from app.voice.microphone.sounddevice_microphone import SounddeviceMicrophone
from app.voice.microphone.stub_microphone import StubMicrophone
from app.voice.providers.stt.faster_whisper import FasterWhisperStt
from app.voice.providers.stt.openai_whisper import OpenAiWhisperStt
from app.voice.providers.stt.stub_stt import StubSpeechToText
from app.voice.providers.tts.edge_tts import EdgeTextToSpeech
from app.voice.providers.tts.openai_tts import OpenAiTts
from app.voice.providers.tts.piper import PiperTextToSpeech
from app.voice.providers.tts.stub_tts import StubTextToSpeech
from app.voice.providers.vad.manual_vad import ManualVoiceActivityDetector
from app.voice.providers.vad.silero_vad import SileroVoiceActivityDetector
from app.voice.providers.vad.stub_vad import StubVoiceActivityDetector
from app.voice.providers.wakeword.openwakeword import OpenWakeWordDetector
from app.voice.providers.wakeword.stub_wakeword import StubWakeWordDetector

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.services.chat import ChatService
    from app.voice.interfaces.audio_output import AudioOutput
    from app.voice.interfaces.microphone import Microphone
    from app.voice.interfaces.speech_to_text import SpeechToText
    from app.voice.interfaces.text_to_speech import TextToSpeech
    from app.voice.interfaces.vad import VoiceActivityDetector
    from app.voice.interfaces.wakeword import WakeWordDetector


@dataclass
class VoicePlatformContainer:
    """Holds wired voice platform components."""

    event_bus: VoiceEventBus
    microphone: Microphone
    wake_word: WakeWordDetector
    vad: VoiceActivityDetector
    stt: SpeechToText
    tts: TextToSpeech
    audio_output: AudioOutput
    conversation: ConversationController
    manager: VoiceManager


def build_microphone(settings: Settings) -> Microphone:
    """Construct the configured microphone adapter."""
    if settings.voice_microphone_provider == VoiceMicrophoneProvider.STUB.value:
        return StubMicrophone(sample_rate=settings.voice_sample_rate)
    return SounddeviceMicrophone(settings)


def build_wake_word(settings: Settings) -> WakeWordDetector:
    """Construct the configured wake word detector."""
    if settings.voice_wakeword_provider == VoiceWakeWordProvider.STUB.value:
        return StubWakeWordDetector(wake_word=settings.voice_wake_word)
    return OpenWakeWordDetector(settings)


def build_vad(settings: Settings) -> VoiceActivityDetector:
    """Construct the configured VAD adapter."""
    if settings.voice_vad_provider == VoiceVadProvider.STUB.value:
        return StubVoiceActivityDetector(speech_ended=True)
    if settings.voice_vad_provider == VoiceVadProvider.MANUAL.value:
        return ManualVoiceActivityDetector(
            silence_timeout_ms=settings.voice_silence_timeout_ms,
        )
    return SileroVoiceActivityDetector(
        silence_timeout_ms=settings.voice_silence_timeout_ms,
    )


def build_speech_to_text(settings: Settings) -> SpeechToText:
    """Construct the configured STT adapter."""
    provider = settings.voice_stt_provider
    if provider == VoiceSttProvider.STUB.value:
        return StubSpeechToText()
    if provider == VoiceSttProvider.FASTER_WHISPER.value:
        return FasterWhisperStt(settings)
    if provider == VoiceSttProvider.OPENAI.value:
        return OpenAiWhisperStt(settings)
    return FasterWhisperStt(settings)


def build_text_to_speech(settings: Settings) -> TextToSpeech:
    """Construct the configured TTS adapter."""
    provider = settings.voice_tts_provider
    if provider == VoiceTtsProvider.STUB.value:
        return StubTextToSpeech()
    if provider == VoiceTtsProvider.PIPER.value:
        return PiperTextToSpeech(settings)
    if provider == VoiceTtsProvider.OPENAI.value:
        return OpenAiTts(settings)
    if provider == VoiceTtsProvider.EDGE.value:
        return EdgeTextToSpeech(settings)
    return PiperTextToSpeech(settings)


def build_audio_output(settings: Settings) -> AudioOutput:
    """Construct the configured audio output adapter."""
    if settings.voice_audio_output_provider == VoiceAudioOutputProvider.STUB.value:
        return StubAudioOutput()
    return QueueAudioPlayer(settings)


def build_voice_platform(
    settings: Settings,
    chat_service: ChatService,
) -> VoicePlatformContainer:
    """Wire the complete voice platform."""
    event_bus = VoiceEventBus()
    microphone = build_microphone(settings)
    wake_word = build_wake_word(settings)
    vad = build_vad(settings)
    stt = build_speech_to_text(settings)
    tts = build_text_to_speech(settings)
    audio_output = build_audio_output(settings)
    conversation = ConversationController(settings, chat_service, tts, event_bus)
    manager = VoiceManager(
        enabled=settings.voice_enabled,
        settings=settings,
        microphone=microphone,
        wake_word=wake_word,
        vad=vad,
        stt=stt,
        conversation=conversation,
        audio_output=audio_output,
        event_bus=event_bus,
        silence_timeout_ms=settings.voice_silence_timeout_ms,
    )
    return VoicePlatformContainer(
        event_bus=event_bus,
        microphone=microphone,
        wake_word=wake_word,
        vad=vad,
        stt=stt,
        tts=tts,
        audio_output=audio_output,
        conversation=conversation,
        manager=manager,
    )
