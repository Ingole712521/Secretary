"""Utility module tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.utils.date import utc_now, utc_timestamp_iso
from app.utils.env import get_env, is_truthy
from app.utils.file import ensure_directory, read_text_file, write_text_file
from app.utils.json import dumps, loads


def test_utc_timestamp_iso_format() -> None:
    """UTC timestamp is ISO 8601 formatted."""
    timestamp = utc_timestamp_iso()
    assert "T" in timestamp


def test_utc_now_is_timezone_aware() -> None:
    """UTC now returns timezone-aware datetime."""
    assert utc_now().tzinfo is not None


def test_json_round_trip() -> None:
    """JSON dumps and loads preserve data."""
    data = {"key": "value", "count": 42}
    assert loads(dumps(data)) == data


def test_is_truthy_recognizes_common_values() -> None:
    """Truthy helper recognizes common true strings."""
    assert is_truthy("true") is True
    assert is_truthy("false") is False
    assert is_truthy(None) is False


def test_file_utilities_round_trip(tmp_path: Path) -> None:
    """File write and read round trip works."""
    target = tmp_path / "nested" / "test.txt"
    write_text_file(target, "hello")
    assert read_text_file(target) == "hello"
    assert target.parent.exists()


def test_ensure_directory_creates_parents(tmp_path: Path) -> None:
    """ensure_directory creates parent directories."""
    target = tmp_path / "a" / "b" / "c"
    ensure_directory(target)
    assert target.is_dir()


def test_get_env_returns_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_env returns default when variable is unset."""
    monkeypatch.delenv("JARVIS_TEST_VAR", raising=False)
    assert get_env("JARVIS_TEST_VAR", "default") == "default"
