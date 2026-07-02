"""Voice platform factory tests."""

from __future__ import annotations

from app.config.settings import Environment, Settings
from app.voice.factory import build_voice_platform


def _settings(tmp_path: object) -> Settings:
    return Settings(
        _env_file=None,
        app_env=Environment.TESTING,
        debug=True,
        log_dir=tmp_path / "logs",  # type: ignore[operator]
        data_dir=tmp_path / "data",  # type: ignore[operator]
        api_secret_key="test-secret-key",
        voice_stt_provider="stub",
        voice_tts_provider="stub",
        voice_vad_provider="manual",
        voice_wakeword_provider="stub",
        voice_microphone_provider="stub",
        voice_audio_output_provider="stub",
    )


def test_build_voice_platform_wires_stub_components(tmp_path: object) -> None:
    """Factory builds a voice platform with stub providers."""
    from unittest.mock import AsyncMock

    settings = _settings(tmp_path)
    chat_service = AsyncMock()
    platform = build_voice_platform(settings, chat_service)  # type: ignore[arg-type]

    assert platform.stt.provider_name == "stub"
    assert platform.tts.provider_name == "stub"
    assert platform.microphone.provider_name == "stub"
    assert platform.wake_word.provider_name == "stub"
    assert platform.manager.state.value == "idle"
