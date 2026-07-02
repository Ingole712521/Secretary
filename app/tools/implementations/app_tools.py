"""Tool for opening applications, files, folders, and URLs."""

from __future__ import annotations

import asyncio
import platform
import subprocess
import sys
from typing import Any

from app.tools.interfaces.base_tool import BaseTool
from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter

# Friendly names the user is likely to say -> actual Windows launch target.
_WINDOWS_APP_ALIASES = {
    "paint": "mspaint",
    "ms paint": "mspaint",
    "calculator": "calc",
    "calc": "calc",
    "command prompt": "cmd",
    "command line": "cmd",
    "terminal": "wt",
    "windows terminal": "wt",
    "powershell": "powershell",
    "file explorer": "explorer",
    "explorer": "explorer",
    "files": "explorer",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings": "ms-settings:",
    "notepad": "notepad",
    "wordpad": "write",
    "word": "winword",
    "ms word": "winword",
    "excel": "excel",
    "ms excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "code editor": "code",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "google chrome": "chrome",
    "snipping tool": "snippingtool",
    "camera": "microsoft.windows.camera:",
    "photos": "ms-photos:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
}


class OpenAppTool(BaseTool):
    """Open (launch) an application, file, folder, or URL by name.

    This is the general-purpose "open X" tool. It launches the target via
    the operating system so the model does not need to craft shell commands
    for common requests like "open chrome", "open notepad", or
    "open https://github.com".

    Attributes:
        _timeout_seconds: Maximum time to wait for the launch to start.
    """

    def __init__(self, *, timeout_seconds: float = 15.0) -> None:
        """Initialize the tool.

        Args:
            timeout_seconds: Timeout for the launch command.
        """
        self._timeout_seconds = timeout_seconds

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "desktop.open"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Open Application"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Open or launch an application, file, folder, or URL on the "
            "user's computer by name. Use this for any 'open X' / 'launch X' "
            "/ 'start X' request, for example 'open chrome', 'open notepad', "
            "'open spotify', 'open https://github.com', or 'open D:\\reports'. "
            "Provide the app/file/URL as the 'target'."
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
                name="target",
                type="string",
                description=(
                    "The application name, file path, folder path, or URL to "
                    "open (e.g. 'chrome', 'notepad', 'https://github.com')."
                ),
                required=True,
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.EXECUTE]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Open the requested target.

        Args:
            params: Must include ``target``.

        Returns:
            Result describing whether the target was launched.
        """
        target = str(params["target"]).strip()
        if not target:
            return ToolResult.failure(
                error="No target provided",
                message="Tell me what to open (an app, file, folder, or URL).",
            )

        launch_target = _resolve_alias(target)

        try:
            exit_code, stderr = await asyncio.to_thread(self._launch, launch_target)
        except subprocess.TimeoutExpired:
            # A launch that does not return quickly usually means the app
            # started and is running in the foreground.
            return ToolResult.success(
                output={"target": target},
                message=f"Launched '{target}'.",
            )
        except OSError as exc:
            return ToolResult.failure(
                error=str(exc),
                message=f"Failed to open '{target}'.",
            )

        if exit_code != 0:
            return ToolResult.failure(
                error=stderr.strip() or f"Exit code {exit_code}",
                message=(
                    f"Could not open '{target}'. It may not be installed or "
                    "the name may be wrong."
                ),
            )

        return ToolResult.success(
            output={"target": target},
            message=f"Opened '{target}'.",
        )

    def _launch(self, target: str) -> tuple[int, str]:
        """Launch the target synchronously and return (exit_code, stderr)."""
        argv = _launch_argv(target)
        completed = subprocess.run(  # noqa: S603
            argv,
            capture_output=True,
            timeout=self._timeout_seconds,
            check=False,
        )
        stderr = completed.stderr.decode(sys.getdefaultencoding(), errors="replace")
        return completed.returncode, stderr


def _resolve_alias(target: str) -> str:
    """Map a friendly app name to its real launch target on Windows.

    URLs, paths, and unknown names are returned unchanged.

    Args:
        target: The user-provided app name, path, or URL.

    Returns:
        The executable/target to launch.
    """
    if platform.system() != "Windows":
        return target
    if "/" in target or "\\" in target or ":" in target or "." in target:
        # Looks like a path or URL; do not remap.
        return target
    return _WINDOWS_APP_ALIASES.get(target.lower(), target)


def _launch_argv(target: str) -> list[str]:
    """Build the OS-specific command to open a target."""
    if platform.system() == "Windows":
        command = f"Start-Process -FilePath {_ps_quote(target)}"
        return [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ]
    if platform.system() == "Darwin":
        return ["open", target]
    return ["xdg-open", target]


def _ps_quote(value: str) -> str:
    """Single-quote a value for safe use in a PowerShell command."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"
