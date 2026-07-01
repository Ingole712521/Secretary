"""Windows desktop adapter tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.tools.desktop.adapters.unsupported import UnsupportedDesktopAutomation
from app.tools.desktop.adapters.windows import WindowsDesktopAutomation
from app.tools.desktop.exceptions import DesktopAutomationError


class _FakeWindow:
    """Fake window object for pygetwindow."""

    def __init__(self, title: str) -> None:
        self.title = title
        self.activated = False

    def activate(self) -> None:
        """Mark window as activated."""
        self.activated = True


@pytest.mark.asyncio
async def test_windows_focus_window_uses_pygetwindow() -> None:
    """focus_window activates the first matching window."""
    fake_window = _FakeWindow("Notepad")

    def get_windows_with_title(title: str) -> list[_FakeWindow]:
        assert title == "Notepad"
        return [fake_window]

    gw = SimpleNamespace(getWindowsWithTitle=get_windows_with_title)
    adapter = WindowsDesktopAutomation(pygetwindow_module=gw, pyautogui_module=object())

    result = await adapter.focus_window("Notepad")

    assert result["focused"] is True
    assert fake_window.activated is True


@pytest.mark.asyncio
async def test_windows_focus_window_missing_target() -> None:
    """focus_window raises when no window matches."""
    gw = SimpleNamespace(getWindowsWithTitle=lambda _title: [])
    adapter = WindowsDesktopAutomation(pygetwindow_module=gw, pyautogui_module=object())

    with pytest.raises(DesktopAutomationError, match="No window found"):
        await adapter.focus_window("Missing")


@pytest.mark.asyncio
async def test_windows_click_invokes_pyautogui() -> None:
    """click delegates to pyautogui.click."""
    calls: list[dict[str, Any]] = []

    def click(**kwargs: Any) -> None:
        calls.append(kwargs)

    pyautogui = SimpleNamespace(
        click=click,
        FAILSAFE=True,
        write=lambda *_a, **_k: None,
    )
    adapter = WindowsDesktopAutomation(
        pyautogui_module=pyautogui,
        pygetwindow_module=object(),
    )

    result = await adapter.click(15, 25, button="left")

    assert result["clicked"] is True
    assert calls == [{"x": 15, "y": 25, "button": "left"}]


@pytest.mark.asyncio
async def test_unsupported_adapter_reports_not_supported() -> None:
    """Unsupported adapter returns is_supported=False."""
    adapter = UnsupportedDesktopAutomation()

    assert adapter.is_supported is False
    with pytest.raises(DesktopAutomationError, match="not supported"):
        await adapter.type_text("hello")
