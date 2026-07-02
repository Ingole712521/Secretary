"""Unit tests for the Cursor open-project tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.tools.implementations import cursor_tools
from app.tools.implementations.cursor_tools import OpenCursorProjectTool


@pytest.fixture
def _recorded_launches(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Capture subprocess launches instead of opening Cursor."""
    launches: list[list[str]] = []

    class _FakePopen:
        def __init__(self, argv: list[str], **_kwargs: Any) -> None:
            launches.append(argv)

    monkeypatch.setattr(cursor_tools.subprocess, "Popen", _FakePopen)
    return launches


def _make_project(root: Path, name: str, *, marker: bool = True) -> Path:
    project = root / name
    project.mkdir(parents=True)
    if marker:
        (project / ".git").mkdir()
    return project


@pytest.mark.asyncio
async def test_finds_and_opens_matching_project(
    tmp_path: Path,
    _recorded_launches: list[list[str]],
) -> None:
    """A matching project is found and opened in Cursor."""
    _make_project(tmp_path, "my-cool-app")
    tool = OpenCursorProjectTool(roots=[str(tmp_path)], max_depth=3)

    result = await tool.execute({"project": "cool app"})

    assert result.is_success
    assert result.output["project_name"] == "my-cool-app"
    assert result.output["opened"].endswith("my-cool-app")
    assert len(_recorded_launches) == 1
    assert str(tmp_path / "my-cool-app") in _recorded_launches[0]


@pytest.mark.asyncio
async def test_fuzzy_underscore_match(
    tmp_path: Path,
    _recorded_launches: list[list[str]],
) -> None:
    """Spaces in the query match underscores/dashes in folder names."""
    _make_project(tmp_path, "ca_kts")
    tool = OpenCursorProjectTool(roots=[str(tmp_path)], max_depth=3)

    result = await tool.execute({"project": "ca kts"})

    assert result.is_success
    assert result.output["project_name"] == "ca_kts"


@pytest.mark.asyncio
async def test_no_match_returns_warning(
    tmp_path: Path,
    _recorded_launches: list[list[str]],
) -> None:
    """A missing project returns a warning without launching Cursor."""
    _make_project(tmp_path, "something-else")
    tool = OpenCursorProjectTool(roots=[str(tmp_path)], max_depth=3)

    result = await tool.execute({"project": "nonexistent-xyz"})

    assert result.status.value == "warning"
    assert result.output["matches"] == []
    assert _recorded_launches == []


@pytest.mark.asyncio
async def test_empty_project_name_fails(
    tmp_path: Path,
    _recorded_launches: list[list[str]],
) -> None:
    """A blank project name is rejected."""
    tool = OpenCursorProjectTool(roots=[str(tmp_path)], max_depth=3)

    result = await tool.execute({"project": "   "})

    assert result.is_failure
    assert _recorded_launches == []


@pytest.mark.asyncio
async def test_exact_match_preferred_over_partial(
    tmp_path: Path,
    _recorded_launches: list[list[str]],
) -> None:
    """An exact name match ranks above a partial match."""
    _make_project(tmp_path, "app-backend")
    _make_project(tmp_path, "app")
    tool = OpenCursorProjectTool(roots=[str(tmp_path)], max_depth=3)

    result = await tool.execute({"project": "app"})

    assert result.is_success
    assert result.output["project_name"] == "app"


@pytest.mark.asyncio
async def test_wordy_query_matches_project(
    tmp_path: Path,
    _recorded_launches: list[list[str]],
) -> None:
    """A query with extra noise words still finds the project folder."""
    _make_project(tmp_path, "alif")
    tool = OpenCursorProjectTool(roots=[str(tmp_path)], max_depth=3)

    result = await tool.execute({"project": "open a alif view name project"})

    assert result.is_success
    assert result.output["project_name"] == "alif"
