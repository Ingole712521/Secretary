"""Unit tests for the open-application tool."""

from __future__ import annotations

import subprocess
from typing import Any

import pytest

from app.tools.implementations import app_tools
from app.tools.implementations.app_tools import OpenAppTool


@pytest.fixture
def _recorded(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Capture launch commands and simulate success."""
    calls: list[list[str]] = []

    class _Completed:
        returncode = 0
        stderr = b""

    def _fake_run(argv: list[str], **_kwargs: Any) -> _Completed:
        calls.append(argv)
        return _Completed()

    monkeypatch.setattr(app_tools.subprocess, "run", _fake_run)
    return calls


@pytest.mark.asyncio
async def test_open_app_launches_target(_recorded: list[list[str]]) -> None:
    """A valid target is launched successfully."""
    tool = OpenAppTool()
    result = await tool.execute({"target": "notepad"})

    assert result.is_success
    assert result.output["target"] == "notepad"
    assert len(_recorded) == 1
    assert any("notepad" in part for part in _recorded[0])


@pytest.mark.asyncio
async def test_open_app_rejects_empty_target(_recorded: list[list[str]]) -> None:
    """A blank target is rejected without launching."""
    tool = OpenAppTool()
    result = await tool.execute({"target": "   "})

    assert result.is_failure
    assert _recorded == []


@pytest.mark.asyncio
async def test_open_app_reports_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-zero exit code produces a failure result."""

    class _Completed:
        returncode = 1
        stderr = b"not found"

    def _fake_run(_argv: list[str], **_kwargs: Any) -> _Completed:
        return _Completed()

    monkeypatch.setattr(app_tools.subprocess, "run", _fake_run)
    tool = OpenAppTool()
    result = await tool.execute({"target": "nonexistent-app-xyz"})

    assert result.is_failure


@pytest.mark.asyncio
async def test_open_app_treats_timeout_as_running(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A launch that blocks (running app) is treated as success."""

    def _fake_run(argv: list[str], **_kwargs: Any) -> object:
        raise subprocess.TimeoutExpired(cmd=argv, timeout=1)

    monkeypatch.setattr(app_tools.subprocess, "run", _fake_run)
    tool = OpenAppTool(timeout_seconds=1)
    result = await tool.execute({"target": "spotify"})

    assert result.is_success
