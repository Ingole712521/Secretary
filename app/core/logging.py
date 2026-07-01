"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING

from app.utils.file import ensure_directory
from app.utils.json import dumps

if TYPE_CHECKING:
    from app.config.settings import Settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record to JSON.

        Args:
            record: Log record to format.

        Returns:
            JSON string.
        """
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "correlation_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return dumps(payload)


def setup_logging(settings: Settings) -> None:
    """Configure root logger with console and rotating file handlers.

    Args:
        settings: Application settings controlling log level and format.
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.log_level.upper())

    formatter: logging.Formatter
    if settings.use_json_logs:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if not settings.is_testing:
        ensure_directory(settings.log_dir)
        file_path = settings.log_dir / settings.log_file_name
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=settings.log_file_max_bytes,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_request_logger() -> logging.Logger:
    """Return the logger used for HTTP request logging."""
    return logging.getLogger("jarvis.request")
