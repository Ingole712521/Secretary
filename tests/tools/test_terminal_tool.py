"""Terminal tool unit tests."""

from __future__ import annotations

import pytest

from app.tools.implementations.terminal import TerminalTool


@pytest.mark.asyncio
async def test_terminal_tool_executes_command_with_mock_runner() -> None:
    """execute() returns stdout and exit code from the runner."""

    async def runner(
        command: str,
        cwd: str | None,
        timeout_seconds: float,
    ) -> tuple[int, str, str]:
        _ = cwd, timeout_seconds
        return 0, f"ran:{command}", ""

    tool = TerminalTool(runner=runner)
    result = await tool.execute({"command": "echo hello"})

    assert result.is_success
    assert result.output["stdout"] == "ran:echo hello"
    assert result.output["exit_code"] == 0


@pytest.mark.asyncio
async def test_terminal_tool_reports_nonzero_exit_as_warning() -> None:
    """Non-zero exit codes produce a warning result."""

    async def runner(
        _command: str,
        _cwd: str | None,
        _timeout_seconds: float,
    ) -> tuple[int, str, str]:
        return 1, "", "failed"

    tool = TerminalTool(runner=runner)
    result = await tool.execute({"command": "exit 1"})

    assert result.status.value == "warning"
    assert result.output["exit_code"] == 1


@pytest.mark.asyncio
async def test_terminal_tool_handles_timeout() -> None:
    """Timeouts return a failure result."""

    async def runner(
        _command: str,
        _cwd: str | None,
        _timeout_seconds: float,
    ) -> tuple[int, str, str]:
        raise TimeoutError

    tool = TerminalTool(runner=runner)
    result = await tool.execute({"command": "sleep 999"})

    assert result.is_failure
    assert "timed out" in (result.error or "").lower()
