"""Desktop automation adapter factory."""

from __future__ import annotations

import platform
from typing import TYPE_CHECKING

from app.tools.desktop.adapters.unsupported import UnsupportedDesktopAutomation
from app.tools.desktop.adapters.windows import WindowsDesktopAutomation

if TYPE_CHECKING:
    from app.tools.desktop.interfaces.desktop_automation import DesktopAutomation


def build_desktop_automation() -> DesktopAutomation:
    """Construct the desktop automation adapter for the current platform.

    Returns:
        Windows adapter on Windows, otherwise an unsupported stub.
    """
    if platform.system() == "Windows":
        return WindowsDesktopAutomation()
    return UnsupportedDesktopAutomation()
