"""Terminal microphone level meter helpers."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path


def format_level_bar(level: float, *, width: int = 28, max_rms: float = 2500.0) -> str:
    """Render a text bar for an RMS microphone level.

    Uses ASCII characters so the meter works in Windows CMD (cp1252).

    Args:
        level: Current RMS energy (0 = silence).
        width: Number of bar characters.
        max_rms: RMS value that maps to a full bar.

    Returns:
        A string like ``########--------------------``.
    """
    pct = max(0.0, min(1.0, level / max_rms))
    filled = int(round(pct * width))
    return "#" * filled + "-" * (width - filled)


def format_meter_line(
    level: float,
    *,
    recording: bool = False,
    width: int = 28,
) -> str:
    """Build one terminal meter line for live display.

    Args:
        level: Current RMS energy.
        recording: Whether speech capture has started.
        width: Bar width in characters.

    Returns:
        A single-line meter string.
    """
    bar = format_level_bar(level, width=width)
    pct = min(100, int(level / 25))
    state = "recording" if recording else "listening"
    return f"Mic [{bar}] {pct:>3}%  {state}"


class MicLevelDisplay:
    """Update a single terminal line with live microphone levels."""

    def __init__(self, *, width: int = 28) -> None:
        """Initialize the display."""
        self._width = width
        self._active = False

    def show(self, level: float, *, recording: bool = False) -> None:
        """Redraw the meter on the current terminal line."""
        line = format_meter_line(level, recording=recording, width=self._width)
        sys.stdout.write(f"\r{line}   ")
        sys.stdout.flush()
        self._active = True

    def clear(self) -> None:
        """Clear the meter line."""
        if not self._active:
            return
        sys.stdout.write("\r" + " " * 72 + "\r")
        sys.stdout.flush()
        self._active = False


def poll_level_file(
    level_path: Path,
    display: MicLevelDisplay,
    *,
    stop_when: Callable[[], bool] | None = None,
    poll_interval: float = 0.05,
) -> None:
    """Poll a sidecar level file and refresh the terminal meter.

    Args:
        level_path: File written as ``rms|started|silence_ms|threshold``.
        display: Meter display to update.
        stop_when: Callable returning True when polling should stop.
        poll_interval: Seconds between refreshes.
    """
    while stop_when is None or not stop_when():
        if level_path.exists():
            try:
                raw = level_path.read_text(encoding="utf-8").strip()
                parts = raw.split("|")
                if len(parts) >= 2:
                    level = float(parts[0])
                    recording = parts[1] == "1"
                    display.show(level, recording=recording)
            except (OSError, ValueError):
                pass
        time.sleep(poll_interval)
