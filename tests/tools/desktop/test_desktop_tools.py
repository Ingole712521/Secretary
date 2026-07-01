"""Desktop tool unit tests."""

from __future__ import annotations

import pytest

from app.tools.implementations.desktop_tools import (
    ClickTool,
    FocusWindowTool,
    ScreenshotRegionTool,
    TypeTextTool,
)
from tests.tools.desktop.mock_desktop import MockDesktopAutomation


@pytest.mark.asyncio
async def test_focus_window_tool() -> None:
    """focus_window delegates to the desktop adapter."""
    desktop = MockDesktopAutomation()
    tool = FocusWindowTool(desktop)

    result = await tool.execute({"title": "Notepad"})

    assert result.is_success
    assert desktop.focused == ["Notepad"]
    assert result.output["focused"] is True


@pytest.mark.asyncio
async def test_type_text_tool() -> None:
    """type_text records text in the desktop adapter."""
    desktop = MockDesktopAutomation()
    tool = TypeTextTool(desktop)

    result = await tool.execute({"text": "hello"})

    assert result.is_success
    assert desktop.typed == ["hello"]


@pytest.mark.asyncio
async def test_click_tool() -> None:
    """click passes coordinates to the desktop adapter."""
    desktop = MockDesktopAutomation()
    tool = ClickTool(desktop)

    result = await tool.execute({"x": 10, "y": 20, "button": "left"})

    assert result.is_success
    assert desktop.clicks[0]["x"] == 10


@pytest.mark.asyncio
async def test_screenshot_region_tool() -> None:
    """screenshot_region returns image metadata."""
    desktop = MockDesktopAutomation()
    tool = ScreenshotRegionTool(desktop)

    result = await tool.execute({"x": 0, "y": 0, "width": 100, "height": 50})

    assert result.is_success
    assert result.output["image_base64"] == "aGVsbG8="
    assert len(desktop.screenshots) == 1


@pytest.mark.asyncio
async def test_desktop_tool_unsupported_platform() -> None:
    """Unsupported platforms return a clear failure result."""
    desktop = MockDesktopAutomation(supported=False)
    tool = FocusWindowTool(desktop)

    result = await tool.execute({"title": "Notepad"})

    assert result.is_failure
    assert "not supported" in (result.error or "").lower()
