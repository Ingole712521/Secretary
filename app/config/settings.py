"""Application settings loaded from environment variables."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Environment(StrEnum):
    """Supported deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


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
    cors_origins: list[str] = Field(
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


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear the cached settings singleton.

    Used in tests and when reloading configuration at runtime.
    """
    get_settings.cache_clear()
