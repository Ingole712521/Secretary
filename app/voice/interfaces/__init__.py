"""Voice platform interface exports."""

from app.voice.interfaces.audio_output import AudioOutput
from app.voice.interfaces.microphone import Microphone
from app.voice.interfaces.speech_to_text import SpeechToText
from app.voice.interfaces.text_to_speech import TextToSpeech
from app.voice.interfaces.vad import VoiceActivityDetector
from app.voice.interfaces.wakeword import WakeWordDetector

__all__ = [
    "AudioOutput",
    "Microphone",
    "SpeechToText",
    "TextToSpeech",
    "VoiceActivityDetector",
    "WakeWordDetector",
]
