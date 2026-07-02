"""Tools for opening projects in the Cursor editor."""

from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

from app.tools.interfaces.base_tool import BaseTool
from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter

# Directories that are never worth scanning for projects.
_SKIP_DIRS = frozenset(
    {
        "node_modules",
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "site-packages",
        "AppData",
        "$Recycle.Bin",
        "Windows",
        "Program Files",
        "Program Files (x86)",
    }
)

# Files/dirs that mark a directory as a real project (for ranking).
_PROJECT_MARKERS = frozenset(
    {
        ".git",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        ".vscode",
        "tsconfig.json",
        "pubspec.yaml",
        "composer.json",
    }
)


class OpenCursorProjectTool(BaseTool):
    """Find a project folder by name and open it in Cursor.

    Instead of opening a blank Cursor window, this tool searches the
    configured project root directories for a folder matching the given
    project name and opens that folder in Cursor.

    Attributes:
        _roots: Directories to search for projects.
        _max_depth: Maximum directory depth to search under each root.
    """

    def __init__(
        self,
        *,
        roots: list[str] | None = None,
        max_depth: int = 3,
    ) -> None:
        """Initialize the tool.

        Args:
            roots: Project root directories. When empty, sensible defaults
                are derived from the user's home and common code folders.
            max_depth: Maximum search depth under each root.
        """
        self._roots = [Path(r) for r in (roots or []) if r]
        self._max_depth = max(1, max_depth)

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "cursor.open_project"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Open Cursor Project"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Search the user's computer for a project folder by name and open "
            "it in the Cursor code editor. Use this whenever the user asks to "
            "open a project, repo, or codebase in Cursor (for example 'open my "
            "react native project in cursor'). Provide the project name the "
            "user mentioned."
        )

    @property
    def category(self) -> ToolCategory:
        """Tool category."""
        return ToolCategory.DEVELOPMENT

    @property
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="project",
                type="string",
                description=(
                    "Name or keyword of the project/folder to find and open "
                    "in Cursor (case-insensitive, partial match allowed)."
                ),
                required=True,
            ),
            ToolParameter(
                name="new_window",
                type="boolean",
                description="Open the project in a new Cursor window.",
                required=False,
                default=False,
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.READ, ToolPermissionLevel.EXECUTE]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Find and open a project in Cursor.

        Args:
            params: Must include ``project``; optional ``new_window``.

        Returns:
            Result describing the opened project or match candidates.
        """
        query = str(params["project"]).strip()
        if not query:
            return ToolResult.failure(
                error="No project name provided",
                message="Tell me which project to open in Cursor.",
            )
        new_window = bool(params.get("new_window", False))

        roots = self._effective_roots()
        matches = await asyncio.to_thread(self._search, query, roots)

        if not matches:
            return ToolResult.warning(
                output={
                    "query": query,
                    "matches": [],
                    "searched_roots": [str(r) for r in roots],
                },
                message=(
                    f"No project matching '{query}' was found under "
                    f"{len(roots)} search location(s)."
                ),
            )

        best = matches[0]
        try:
            await self._open_in_cursor(best, new_window=new_window)
        except OSError as exc:
            return ToolResult.failure(
                error=str(exc),
                message=f"Found '{best.name}' but failed to launch Cursor.",
            )

        return ToolResult.success(
            output={
                "query": query,
                "opened": str(best),
                "project_name": best.name,
                "new_window": new_window,
                "other_matches": [str(p) for p in matches[1:5]],
            },
            message=f"Opened '{best.name}' in Cursor ({best}).",
        )

    def _effective_roots(self) -> list[Path]:
        """Return the configured roots or sensible defaults."""
        if self._roots:
            return [r for r in self._roots if r.exists()]
        return _default_project_roots()

    def _search(self, query: str, roots: list[Path]) -> list[Path]:
        """Search roots for directories matching ``query``.

        Args:
            query: Case-insensitive project name/keyword.
            roots: Directories to search.

        Returns:
            Matching directories ranked best-first.
        """
        query_lower = query.lower()
        query_slug = _slug(query)
        scored: list[tuple[int, int, Path]] = []
        seen: set[Path] = set()

        for root in roots:
            for directory, depth in _walk(root, self._max_depth):
                if directory in seen:
                    continue
                seen.add(directory)
                score = _match_score(directory.name, query_lower, query_slug)
                if score <= 0:
                    continue
                if _looks_like_project(directory):
                    score += 40
                scored.append((score, -depth, directory))

        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [path for _, _, path in scored]

    async def _open_in_cursor(self, path: Path, *, new_window: bool) -> None:
        """Launch Cursor for the given folder without blocking.

        Args:
            path: Project directory to open.
            new_window: Whether to force a new window.

        Raises:
            OSError: When the Cursor process cannot be started.
        """
        argv = _cursor_argv(path, new_window=new_window)

        def _launch() -> None:
            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen(  # noqa: S603
                argv,
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        await asyncio.to_thread(_launch)


def _cursor_argv(path: Path, *, new_window: bool) -> list[str]:
    """Build the argument vector to open a folder in Cursor."""
    if os.name == "nt":
        # cursor is a .cmd shim on Windows; invoke via cmd.exe.
        inner = ["cursor"]
        if new_window:
            inner.append("--new-window")
        inner.append(str(path))
        return ["cmd", "/c", *inner]
    argv = ["cursor"]
    if new_window:
        argv.append("--new-window")
    argv.append(str(path))
    return argv


def _default_project_roots() -> list[Path]:
    """Derive default project search roots for this machine."""
    home = Path.home()
    candidates = [
        home / "Documents",
        home / "Desktop",
        home / "source" / "repos",
        home / "source",
        home / "repos",
        home / "Projects",
        home / "projects",
        home / "dev",
        home / "Development",
        home / "code",
        home / "workspace",
        home / "git",
        home,
    ]
    roots = [c for c in candidates if c.exists()]
    if os.name == "nt":
        roots.extend(_windows_drive_roots())
    return _dedupe(roots)


def _windows_drive_roots() -> list[Path]:
    """Return existing fixed-drive roots on Windows (e.g. C:\\, D:\\)."""
    roots: list[Path] = []
    for letter in "CDEFGH":
        drive = Path(f"{letter}:\\")
        if drive.exists():
            roots.append(drive)
    return roots


def _dedupe(paths: list[Path]) -> list[Path]:
    """Remove duplicate paths while preserving order."""
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(path)
    return result


def _walk(root: Path, max_depth: int) -> list[tuple[Path, int]]:
    """List subdirectories under ``root`` up to ``max_depth``.

    Args:
        root: Directory to start from.
        max_depth: Maximum depth relative to root.

    Returns:
        Pairs of (directory, depth).
    """
    if not root.is_dir():
        return []
    results: list[tuple[Path, int]] = []
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        current, depth = stack.pop()
        if depth >= max_depth:
            continue
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue
            name = entry.name
            if name.startswith(".") or name in _SKIP_DIRS:
                continue
            child = Path(entry.path)
            results.append((child, depth + 1))
            stack.append((child, depth + 1))
    return results


def _match_score(name: str, query_lower: str, query_slug: str) -> int:
    """Score how well a directory name matches the query.

    Handles exact, prefix, and substring matches, and also tolerates
    wordy queries where the user adds noise words around the real project
    name (e.g. "alif view name" should still match the folder "alif").
    """
    name_lower = name.lower()
    name_slug = _slug(name)
    if not name_slug:
        return 0

    if name_lower == query_lower or name_slug == query_slug:
        return 100
    if name_slug.startswith(query_slug) or name_lower.startswith(query_lower):
        return 70
    if query_slug and query_slug in name_slug:
        return 55
    if query_lower in name_lower:
        return 50
    # Query contains the folder name plus extra words: "alif view name".
    if len(name_slug) >= 3 and name_slug in query_slug:
        return 48

    # Fall back to per-word matching against the query's tokens.
    best = 0
    for token in _tokens(query_lower):
        token_slug = _slug(token)
        if len(token_slug) < 2:
            continue
        if name_slug == token_slug:
            best = max(best, 60)
        elif len(token_slug) >= 3 and name_slug.startswith(token_slug):
            best = max(best, 40)
        elif len(token_slug) >= 4 and token_slug in name_slug:
            best = max(best, 30)
    return best


def _tokens(value: str) -> list[str]:
    """Split a phrase into alphanumeric word tokens."""
    token: list[str] = []
    tokens: list[str] = []
    for ch in value:
        if ch.isalnum():
            token.append(ch)
        elif token:
            tokens.append("".join(token))
            token = []
    if token:
        tokens.append("".join(token))
    return tokens


def _slug(value: str) -> str:
    """Normalize a string to alphanumeric lowercase for fuzzy matching."""
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _looks_like_project(directory: Path) -> bool:
    """Return True when the directory contains project marker files."""
    try:
        for entry in os.scandir(directory):
            if entry.name in _PROJECT_MARKERS:
                return True
    except OSError:
        return False
    return False
