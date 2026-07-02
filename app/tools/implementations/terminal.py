"""Terminal command execution tool."""

from __future__ import annotations

import asyncio
import platform
import subprocess
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from app.tools.interfaces.base_tool import BaseTool
from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter

CommandRunner = Callable[
    [str, str | None, float],
    Awaitable[tuple[int, str, str]],
]

class TerminalTool(BaseTool):
    """Execute shell commands on the host machine.

  Primary shell is PowerShell on Windows and ``sh`` elsewhere. Commands
  are subject to the tool platform security policy.

  Attributes:
      _timeout_seconds: Maximum command runtime.
      _runner: Injectable command runner for tests.
  """

    def __init__(
        self,
        *,
        timeout_seconds: float = 30.0,
        runner: CommandRunner | None = None,
    ) -> None:
        """Initialize the terminal tool.

        Args:
            timeout_seconds: Command timeout in seconds.
            runner: Optional async runner override for testing.
        """
        self._timeout_seconds = timeout_seconds
        self._runner = runner

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "terminal.run"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Terminal"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Run a shell command on the user's computer and return stdout, "
            "stderr, and exit code. Use PowerShell commands on Windows."
        )

    @property
    def category(self) -> ToolCategory:
        """Tool category."""
        return ToolCategory.SYSTEM

    @property
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="command",
                type="string",
                description="Shell command to execute",
                required=True,
            ),
            ToolParameter(
                name="cwd",
                type="string",
                description="Optional working directory for the command",
                required=False,
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.EXECUTE]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute a shell command.

        Args:
            params: Must include ``command``; optional ``cwd``.

        Returns:
            Structured result with stdout, stderr, and exit code.
        """
        command = str(params["command"])
        cwd = params.get("cwd")
        # Models routinely send optional string params as "" (empty string)
        # rather than omitting them. An empty/blank cwd is not a real working
        # directory and would crash the subprocess (e.g. WinError 123), so
        # treat it as "not provided".
        cwd_str = str(cwd).strip() or None if cwd is not None else None

        try:
            exit_code, stdout, stderr = await self._run_command(
                command,
                cwd_str,
                self._timeout_seconds,
            )
        except TimeoutError:
            return ToolResult.failure(
                error="Command timed out",
                message=f"Command exceeded {self._timeout_seconds}s timeout",
            )
        except OSError as exc:
            return ToolResult.failure(
                error=str(exc),
                message="Failed to start shell process",
            )

        output = {
            "command": command,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "shell": self._shell_name(),
        }

        if exit_code == 0:
            return ToolResult.success(
                output=output,
                message="Command completed successfully",
            )

        return ToolResult.warning(
            output=output,
            message=f"Command exited with code {exit_code}",
        )

    async def _run_command(
        self,
        command: str,
        cwd: str | None,
        timeout_seconds: float,
    ) -> tuple[int, str, str]:
        """Run a command via subprocess or injected runner."""
        if self._runner is not None:
            return await self._runner(command, cwd, timeout_seconds)
        return await _default_command_runner(command, cwd, timeout_seconds)

    @staticmethod
    def _shell_name() -> str:
        """Return the shell name used on the current platform."""
        return "powershell" if platform.system() == "Windows" else "sh"


def _command_argv(command: str) -> list[str]:
    """Build the shell argument vector for the current platform."""
    if platform.system() == "Windows":
        return [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ]
    return ["sh", "-c", command]


async def _default_command_runner(
    command: str,
    cwd: str | None,
    timeout_seconds: float,
) -> tuple[int, str, str]:
    """Execute a command in a worker thread.

    A synchronous ``subprocess.run`` is used inside ``asyncio.to_thread``
    instead of ``asyncio.create_subprocess_exec``. On Windows, uvicorn runs
    on a ``SelectorEventLoop``, which does not support asyncio subprocesses
    and raises an empty ``NotImplementedError``. Running in a thread makes
    command execution work regardless of the active event loop policy.

    Args:
        command: Shell command string.
        cwd: Optional working directory.
        timeout_seconds: Timeout in seconds.

    Returns:
        Tuple of exit code, stdout, and stderr.

    Raises:
        TimeoutError: When the command exceeds the timeout.
        OSError: When the process cannot be started.
    """
    argv = _command_argv(command)
    encoding = sys.getdefaultencoding()

    def _run() -> tuple[int, str, str]:
        try:
            completed = subprocess.run(  # noqa: S603
                argv,
                capture_output=True,
                cwd=cwd,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(str(exc)) from exc
        stdout = completed.stdout.decode(encoding, errors="replace")
        stderr = completed.stderr.decode(encoding, errors="replace")
        return completed.returncode, stdout, stderr

    return await asyncio.to_thread(_run)
