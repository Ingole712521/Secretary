"""Configuration system tests."""

from __future__ import annotations

import pytest

from app.config.settings import Environment, Settings


def test_settings_defaults_to_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings default environment is development."""
    monkeypatch.delenv("APP_ENV", raising=False)
    settings = Settings(_env_file=None)
    assert settings.app_env == Environment.DEVELOPMENT


def test_settings_testing_environment() -> None:
    """Testing environment is recognized correctly."""
    settings = Settings(_env_file=None, app_env=Environment.TESTING)
    assert settings.is_testing is True
    assert settings.is_production is False


def test_settings_parses_cors_origins_from_string() -> None:
    """CORS origins parse from comma-separated string."""
    settings = Settings(
        _env_file=None,
        cors_origins="http://a.com, http://b.com",
    )
    assert settings.cors_origins == ["http://a.com", "http://b.com"]


def test_settings_production_rejects_default_secret() -> None:
    """Production environment rejects the default API secret key."""
    with pytest.raises(ValueError, match="API_SECRET_KEY"):
        Settings(
            _env_file=None,
            app_env=Environment.PRODUCTION,
            debug=False,
            api_secret_key="change-me-in-production",
        )


def test_settings_production_rejects_debug_mode() -> None:
    """Production environment rejects debug mode."""
    with pytest.raises(ValueError, match="DEBUG"):
        Settings(
            _env_file=None,
            app_env=Environment.PRODUCTION,
            debug=True,
            api_secret_key="secure-production-key",
        )


def test_settings_use_json_logs_in_production() -> None:
    """JSON logging is enabled in production by default."""
    settings = Settings(
        _env_file=None,
        app_env=Environment.PRODUCTION,
        debug=False,
        api_secret_key="secure-production-key",
    )
    assert settings.use_json_logs is True
