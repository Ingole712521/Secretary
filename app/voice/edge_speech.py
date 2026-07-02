"""Smooth neural text-to-speech using Edge TTS with local playback.

Edge TTS provides natural-sounding neural voices for free. Synthesis needs
an internet connection; playback is local via the Windows WPF MediaPlayer,
so no extra audio packages are required.
"""

from __future__ import annotations

import asyncio
import platform
import subprocess
import tempfile
import uuid
from pathlib import Path

import edge_tts

# WPF MediaPlayer can play mp3 offline without any extra dependencies.
_PLAY_SCRIPT = """param([string]$Path)
Add-Type -AssemblyName PresentationCore
$p = New-Object System.Windows.Media.MediaPlayer
$p.Open([uri]$Path)
$waited = 0
while (-not $p.NaturalDuration.HasTimeSpan -and $waited -lt 100) {
    Start-Sleep -Milliseconds 50; $waited++
}
$p.Play()
if ($p.NaturalDuration.HasTimeSpan) {
    $ms = $p.NaturalDuration.TimeSpan.TotalMilliseconds
    Start-Sleep -Milliseconds ([int]$ms + 400)
} else {
    Start-Sleep -Seconds 6
}
$p.Stop(); $p.Close()
"""


class EdgeSpeechError(RuntimeError):
    """Raised when neural speech synthesis or playback fails."""


class EdgeSpeaker:
    """Speak text using a smooth Edge TTS neural voice.

    Attributes:
        _voice: Edge neural voice name (e.g. ``en-US-JennyNeural``).
        _rate: Speaking rate adjustment (e.g. ``+0%``, ``-10%``).
        _work_dir: Temp directory for audio files and the play script.
    """

    def __init__(
        self,
        *,
        voice: str = "en-US-JennyNeural",
        rate: str = "+0%",
    ) -> None:
        """Initialize the speaker and materialize the playback script.

        Args:
            voice: Edge neural voice name.
            rate: Rate adjustment string accepted by Edge TTS.
        """
        self._voice = voice
        self._rate = rate
        self._work_dir = Path(tempfile.gettempdir()) / "jarvis_voice"
        self._work_dir.mkdir(parents=True, exist_ok=True)
        self._play_script = self._work_dir / "play.ps1"
        if platform.system() == "Windows":
            self._play_script.write_text(_PLAY_SCRIPT, encoding="utf-8")

    async def speak(self, text: str) -> None:
        """Synthesize and play text aloud.

        Args:
            text: Text to speak. Empty text is ignored.

        Raises:
            EdgeSpeechError: When synthesis or playback fails.
        """
        clean = (text or "").strip()
        if not clean:
            return

        mp3 = self._work_dir / f"edge_{uuid.uuid4().hex}.mp3"
        try:
            await self._synthesize(clean, mp3)
            await asyncio.to_thread(self._play, mp3)
        except EdgeSpeechError:
            raise
        except Exception as exc:  # noqa: BLE001
            msg = f"Neural speech failed: {exc}"
            raise EdgeSpeechError(msg) from exc
        finally:
            mp3.unlink(missing_ok=True)

    async def _synthesize(self, text: str, mp3: Path) -> None:
        """Render text to an mp3 file with Edge TTS."""
        communicate = edge_tts.Communicate(text, self._voice, rate=self._rate)
        await communicate.save(str(mp3))
        if not mp3.exists() or mp3.stat().st_size == 0:
            msg = "Edge TTS produced no audio (check internet connection)."
            raise EdgeSpeechError(msg)

    def _play(self, mp3: Path) -> None:
        """Play an mp3 file locally via the WPF MediaPlayer."""
        if platform.system() != "Windows":
            msg = "Neural playback currently supports Windows only."
            raise EdgeSpeechError(msg)
        completed = subprocess.run(  # noqa: S603
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(self._play_script),
                "-Path",
                str(mp3),
            ],
            capture_output=True,
            timeout=120.0,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            msg = f"Audio playback failed: {detail or 'unknown error'}"
            raise EdgeSpeechError(msg)
