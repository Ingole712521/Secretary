"""Desktop automation adapter exports."""

from app.tools.desktop.adapters.unsupported import UnsupportedDesktopAutomation
from app.tools.desktop.adapters.windows import WindowsDesktopAutomation

__all__ = ["UnsupportedDesktopAutomation", "WindowsDesktopAutomation"]
