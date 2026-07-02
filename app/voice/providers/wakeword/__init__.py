"""Wake word provider exports."""

from app.voice.providers.wakeword.openwakeword import OpenWakeWordDetector
from app.voice.providers.wakeword.stub_wakeword import StubWakeWordDetector

__all__ = ["OpenWakeWordDetector", "StubWakeWordDetector"]
