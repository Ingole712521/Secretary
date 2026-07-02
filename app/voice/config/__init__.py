"""Voice platform configuration."""

from app.voice.config.enums import (
    VoiceAudioOutputProvider,
    VoiceMicrophoneProvider,
    VoiceSttProvider,
    VoiceTtsProvider,
    VoiceVadProvider,
    VoiceWakeWordProvider,
)
from app.voice.config.platform_config import (
    VoicePlatformConfig,
    build_voice_platform_config,
)

__all__ = [
    "VoiceAudioOutputProvider",
    "VoiceMicrophoneProvider",
    "VoicePlatformConfig",
    "VoiceSttProvider",
    "VoiceTtsProvider",
    "VoiceVadProvider",
    "VoiceWakeWordProvider",
    "build_voice_platform_config",
]
