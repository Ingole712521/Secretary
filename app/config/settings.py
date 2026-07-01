"""Application settings loaded from environment variables."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Environment(StrEnum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProviderSetting(StrEnum):
    """Active LLM provider selection from environment configuration.

    Values align with ``LLMProviderName`` in ``app.brain.schemas.llm``.
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"


class Settings(BaseSettings):
    """Central configuration for Jarvis OS.

    All values are loaded from environment variables or a ``.env`` file.
    Secrets must never be hardcoded in source code.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # Application
    app_name: str = Field(default="Jarvis OS", alias="APP_NAME")
    app_env: Environment = Field(default=Environment.DEVELOPMENT, alias="APP_ENV")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_prefix: str = Field(default="/v1", alias="API_PREFIX")

    # Security
    api_secret_key: SecretStr = Field(
        default=SecretStr("change-me-in-production"),
        alias="API_SECRET_KEY",
    )
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="CORS_ORIGINS",
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")
    log_dir: Path = Field(default=PROJECT_ROOT / "logs", alias="LOG_DIR")
    log_file_name: str = Field(default="jarvis.log", alias="LOG_FILE_NAME")
    log_file_max_bytes: int = Field(default=10_485_760, alias="LOG_FILE_MAX_BYTES")
    log_file_backup_count: int = Field(default=5, alias="LOG_FILE_BACKUP_COUNT")
    correlation_id_header: str = Field(
        default="X-Correlation-ID",
        alias="CORRELATION_ID_HEADER",
    )

    # Data
    data_dir: Path = Field(default=PROJECT_ROOT / "data", alias="DATA_DIR")

    # LLM / AI (loaded from env; adapters not connected until Sprint 3)
    llm_provider: LLMProviderSetting = Field(
        default=LLMProviderSetting.OPENAI,
        alias="LLM_PROVIDER",
    )
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_api_base: str | None = Field(default=None, alias="OPENAI_API_BASE")
    openrouter_api_key: SecretStr | None = Field(
        default=None,
        alias="OPENROUTER_API_KEY",
    )
    openrouter_model: str = Field(
        default="openrouter/auto",
        alias="OPENROUTER_MODEL",
    )
    openrouter_api_base: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_API_BASE",
    )
    jarvis_system_prompt: str = Field(
        default=(
            "You are Jarvis, a personal AI assistant for the user's computer. "
            "Be helpful, concise, and proactive. You remember the current "
            "conversation. When you cannot do something yet, say so clearly. "
            "Use the terminal tool to inspect or change the system when needed. "
            "Use desktop tools (focus_window, type_text, click, screenshot_region) "
            "to interact with applications on screen."
        ),
        alias="JARVIS_SYSTEM_PROMPT",
    )
    tools_enabled: bool = Field(default=True, alias="TOOLS_ENABLED")
    desktop_automation_enabled: bool = Field(
        default=True,
        alias="DESKTOP_AUTOMATION_ENABLED",
    )
    terminal_command_timeout: int = Field(default=30, alias="TERMINAL_COMMAND_TIMEOUT")
    chat_max_tool_iterations: int = Field(default=5, alias="CHAT_MAX_TOOL_ITERATIONS")
    memory_enabled: bool = Field(default=True, alias="MEMORY_ENABLED")
    memory_db_path: Path | None = Field(default=None, alias="MEMORY_DB_PATH")
    memory_search_limit: int = Field(default=10, alias="MEMORY_SEARCH_LIMIT")
    memory_context_limit: int = Field(default=5, alias="MEMORY_CONTEXT_LIMIT")
    voice_enabled: bool = Field(default=True, alias="VOICE_ENABLED")
    voice_stt_provider: str = Field(default="openai", alias="VOICE_STT_PROVIDER")
    voice_tts_provider: str = Field(default="edge", alias="VOICE_TTS_PROVIDER")
    openai_whisper_model: str = Field(default="whisper-1", alias="OPENAI_WHISPER_MODEL")
    openai_tts_model: str = Field(default="tts-1", alias="OPENAI_TTS_MODEL")
    openai_tts_voice: str = Field(default="alloy", alias="OPENAI_TTS_VOICE")
    edge_tts_voice: str = Field(
        default="en-US-GuyNeural",
        alias="EDGE_TTS_VOICE",
    )
    anthropic_api_key: SecretStr | None = Field(
        default=None,
        alias="ANTHROPIC_API_KEY",
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        alias="ANTHROPIC_MODEL",
    )
    gemini_api_key: SecretStr | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    deepseek_api_key: SecretStr | None = Field(
        default=None,
        alias="DEEPSEEK_API_KEY",
    )
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )
    ollama_model: str = Field(default="llama3", alias="OLLAMA_MODEL")
    lm_studio_base_url: str = Field(
        default="http://localhost:1234/v1",
        alias="LM_STUDIO_BASE_URL",
    )
    lm_studio_model: str = Field(default="local-model", alias="LM_STUDIO_MODEL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Parse comma-separated CORS origins from environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("log_dir", "data_dir", mode="before")
    @classmethod
    def parse_path(cls, value: str | Path) -> Path:
        """Coerce string paths to ``Path`` objects."""
        return Path(value) if isinstance(value, str) else value

    @field_validator("memory_db_path", mode="before")
    @classmethod
    def parse_optional_path(cls, value: str | Path | None) -> Path | None:
        """Coerce optional memory DB path strings to ``Path`` objects."""
        if value is None or value == "":
            return None
        return Path(value) if isinstance(value, str) else value

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Normalize log level to uppercase."""
        return value.upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_environment_rules(self) -> Self:
        """Apply environment-specific validation rules."""
        if self.app_env == Environment.PRODUCTION:
            if self.debug:
                msg = "DEBUG must be disabled in production"
                raise ValueError(msg)
            if self.api_secret_key.get_secret_value() == "change-me-in-production":
                msg = "API_SECRET_KEY must be set in production"
                raise ValueError(msg)
        if (
            self.app_env == Environment.STAGING
            and self.api_secret_key.get_secret_value() == "change-me-in-production"
        ):
            msg = "API_SECRET_KEY must be set in staging"
            raise ValueError(msg)
        if self.app_env == Environment.TESTING:
            self.log_json = False
        return self

    @property
    def is_development(self) -> bool:
        """Return True when running in development mode."""
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Return True when running in testing mode."""
        return self.app_env == Environment.TESTING

    @property
    def is_production(self) -> bool:
        """Return True when running in production mode."""
        return self.app_env == Environment.PRODUCTION

    @property
    def use_json_logs(self) -> bool:
        """Return True when structured JSON logging is enabled."""
        return self.log_json or self.is_production

    @property
    def has_llm_credentials(self) -> bool:
        """Return True when credentials exist for the configured LLM provider."""
        return self.get_active_llm_api_key() is not None

    def get_voice_stt_api_key(self) -> SecretStr | None:
        """Return an OpenAI API key suitable for Whisper STT.

        OpenRouter keys (``sk-or-``) are not valid for the Whisper endpoint.
        A direct OpenAI key in ``OPENAI_API_KEY`` is required.

        Returns:
            OpenAI API key, or None if not configured.
        """
        if self.openai_api_key is None:
            return None
        key_value = self.openai_api_key.get_secret_value()
        if key_value.startswith("sk-or-"):
            return None
        return self.openai_api_key

    def get_active_llm_api_key(self) -> SecretStr | None:
        """Return the API key for the currently configured LLM provider.

        For OpenRouter, checks ``OPENROUTER_API_KEY`` first, then falls back
        to ``OPENAI_API_KEY`` when it uses the ``sk-or-v1-`` key format.

        Returns:
            Provider API key, or None if not configured.
        """
        key_map: dict[LLMProviderSetting, SecretStr | None] = {
            LLMProviderSetting.OPENAI: self.openai_api_key,
            LLMProviderSetting.OPENROUTER: self._resolve_openrouter_key(),
            LLMProviderSetting.ANTHROPIC: self.anthropic_api_key,
            LLMProviderSetting.GEMINI: self.gemini_api_key,
            LLMProviderSetting.DEEPSEEK: self.deepseek_api_key,
            LLMProviderSetting.OLLAMA: None,
            LLMProviderSetting.LM_STUDIO: None,
        }
        return key_map.get(self.llm_provider)

    def get_active_llm_model(self) -> str:
        """Return the model name for the currently configured LLM provider.

        Returns:
            Provider-specific model identifier.
        """
        model_map: dict[LLMProviderSetting, str] = {
            LLMProviderSetting.OPENAI: self.openai_model,
            LLMProviderSetting.OPENROUTER: self.openrouter_model,
            LLMProviderSetting.ANTHROPIC: self.anthropic_model,
            LLMProviderSetting.GEMINI: self.gemini_model,
            LLMProviderSetting.DEEPSEEK: self.deepseek_model,
            LLMProviderSetting.OLLAMA: self.ollama_model,
            LLMProviderSetting.LM_STUDIO: self.lm_studio_model,
        }
        return model_map[self.llm_provider]

    def _resolve_openrouter_key(self) -> SecretStr | None:
        """Resolve OpenRouter API key from provider-specific or legacy env vars."""
        if self.openrouter_api_key is not None:
            return self.openrouter_api_key
        if self.openai_api_key is not None:
            key_value = self.openai_api_key.get_secret_value()
            if key_value.startswith("sk-or-"):
                return self.openai_api_key
        return None


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear the cached settings singleton.

    Used in tests and when reloading configuration at runtime.
    """
    get_settings.cache_clear()
