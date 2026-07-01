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


def test_settings_loads_openrouter_api_key() -> None:
    """OpenRouter API key loads from environment field."""
    settings = Settings(
        _env_file=None,
        llm_provider="openrouter",
        openrouter_api_key="sk-or-test-key",  # noqa: S106
    )
    assert settings.llm_provider == "openrouter"
    assert settings.has_llm_credentials is True
    key = settings.get_active_llm_api_key()
    assert key is not None
    assert key.get_secret_value() == "sk-or-test-key"


def test_settings_openrouter_fallback_from_openai_key() -> None:
    """OpenRouter accepts sk-or-v1- keys stored in OPENAI_API_KEY."""
    settings = Settings(
        _env_file=None,
        llm_provider="openrouter",
        openai_api_key="sk-or-v1-legacy-key",  # noqa: S106
    )
    assert settings.has_llm_credentials is True
    assert settings.get_active_llm_api_key() is not None
    assert settings.get_active_llm_api_key().get_secret_value() == "sk-or-v1-legacy-key"


def test_settings_get_active_llm_model() -> None:
    """Active model resolves per provider."""
    settings = Settings(
        _env_file=None,
        llm_provider="openrouter",
        openrouter_model="anthropic/claude-3.5-sonnet",
    )
    assert settings.get_active_llm_model() == "anthropic/claude-3.5-sonnet"


def test_settings_openai_without_key_has_no_credentials() -> None:
    """OpenAI provider without key reports no credentials."""
    settings = Settings(
        _env_file=None,
        llm_provider="openai",
        openai_api_key=None,
    )
    assert settings.has_llm_credentials is False
