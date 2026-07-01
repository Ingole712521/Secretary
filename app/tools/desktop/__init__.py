"""Desktop automation port and adapters."""

from app.tools.desktop.factory import build_desktop_automation
from app.tools.desktop.interfaces.desktop_automation import DesktopAutomation

__all__ = ["DesktopAutomation", "build_desktop_automation"]
