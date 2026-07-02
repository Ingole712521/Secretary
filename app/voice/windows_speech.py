"""Offline Windows speech (SAPI) helpers for the terminal voice assistant.

Uses the built-in .NET ``System.Speech`` APIs via PowerShell, so no extra
Python packages, model downloads, or internet connection are required for
speaking and listening on Windows.
"""

from __future__ import annotations

import platform
import subprocess
import tempfile
import uuid
from pathlib import Path

_SPEAK_SCRIPT = """param([string]$Path, [int]$Rate = 1, [string]$Voice = "female")
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = $Rate
try {
    if ($Voice -eq "female") {
        $s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female)
    } elseif ($Voice -eq "male") {
        $s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Male)
    } elseif ($Voice) {
        $match = $s.GetInstalledVoices() | Where-Object {
            $_.VoiceInfo.Name -like ("*" + $Voice + "*")
        } | Select-Object -First 1
        if ($match) { $s.SelectVoice($match.VoiceInfo.Name) }
    }
} catch {}
$text = Get-Content -Raw -Encoding UTF8 -LiteralPath $Path
if ($text) { $s.Speak($text) }
$s.Dispose()
"""

_LISTEN_SCRIPT = """param([string]$OutPath, [int]$InitialTimeout = 15, `
    [double]$EndSilence = 1.3, [string]$WavPath = "")
Add-Type -AssemblyName System.Speech
# Prefer the en-US recognizer for the best accuracy; fall back to default.
try {
    $culture = New-Object System.Globalization.CultureInfo("en-US")
    $r = New-Object System.Speech.Recognition.SpeechRecognitionEngine $culture
} catch {
    $r = New-Object System.Speech.Recognition.SpeechRecognitionEngine
}
$r.SetInputToDefaultAudioDevice()
$r.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$r.InitialSilenceTimeout = [TimeSpan]::FromSeconds($InitialTimeout)
# Longer trailing silence so natural mid-sentence pauses do not cut you off.
$r.EndSilenceTimeout = [TimeSpan]::FromSeconds($EndSilence)
$r.EndSilenceTimeoutAmbiguous = [TimeSpan]::FromSeconds($EndSilence)
# Allow long utterances instead of stopping after a few seconds of speech.
$r.BabbleTimeout = [TimeSpan]::FromSeconds(0)
$text = ""
try {
    $res = $r.Recognize()
    if ($res) {
        $text = $res.Text
        # Persist the captured audio so a cloud engine can re-transcribe it.
        if ($WavPath -and $res.Audio) {
            $fs = [System.IO.File]::Create($WavPath)
            try { $res.Audio.WriteToWaveStream($fs) } finally { $fs.Close() }
        }
    }
} catch {}
[System.IO.File]::WriteAllText($OutPath, $text, `
    (New-Object System.Text.UTF8Encoding($false)))
$r.Dispose()
"""


class WindowsSpeechError(RuntimeError):
    """Raised when Windows speech is unavailable or fails."""


class WindowsSpeech:
    """Speak and listen using the Windows SAPI speech engine.

    Attributes:
        _rate: Speech rate for synthesis (-10 slow .. 10 fast).
        _voice: Voice preference ("female", "male", or a name substring).
        _work_dir: Temp directory holding the PowerShell helper scripts.
    """

    def __init__(self, *, rate: int = 1, voice: str = "female") -> None:
        """Initialize and materialize the PowerShell helper scripts.

        Args:
            rate: Speech synthesis rate (-10..10).
            voice: Voice selection: "female", "male", or part of an installed
                voice name (e.g. "Zira"). Falls back to the default voice
                when no match is found.

        Raises:
            WindowsSpeechError: When not running on Windows.
        """
        if platform.system() != "Windows":
            msg = "WindowsSpeech requires Windows (System.Speech)."
            raise WindowsSpeechError(msg)
        self._rate = rate
        self._voice = voice
        self._work_dir = Path(tempfile.gettempdir()) / "jarvis_voice"
        self._work_dir.mkdir(parents=True, exist_ok=True)
        self._speak_script = self._work_dir / "speak.ps1"
        self._listen_script = self._work_dir / "listen.ps1"
        self._speak_script.write_text(_SPEAK_SCRIPT, encoding="utf-8")
        self._listen_script.write_text(_LISTEN_SCRIPT, encoding="utf-8")

    def speak(self, text: str) -> None:
        """Speak text aloud synchronously.

        Args:
            text: Text to synthesize. Empty text is ignored.
        """
        clean = (text or "").strip()
        if not clean:
            return
        text_file = self._work_dir / f"say_{uuid.uuid4().hex}.txt"
        text_file.write_text(clean, encoding="utf-8")
        try:
            self._run_powershell(
                self._speak_script,
                [
                    "-Path",
                    str(text_file),
                    "-Rate",
                    str(self._rate),
                    "-Voice",
                    self._voice,
                ],
                timeout=120.0,
            )
        finally:
            text_file.unlink(missing_ok=True)

    def listen(
        self,
        *,
        initial_timeout: int = 15,
        end_silence: float = 1.3,
        capture_wav: Path | None = None,
    ) -> str:
        """Listen on the default microphone and return recognized text.

        Args:
            initial_timeout: Seconds to wait for speech to begin.
            end_silence: Trailing silence (seconds) that ends a phrase.
            capture_wav: When set, the raw recorded phrase is written to this
                WAV path so a higher-accuracy engine can re-transcribe it.

        Returns:
            Recognized text, or an empty string when nothing was heard.
        """
        out_file = self._work_dir / f"heard_{uuid.uuid4().hex}.txt"
        args = [
            "-OutPath",
            str(out_file),
            "-InitialTimeout",
            str(initial_timeout),
            "-EndSilence",
            str(end_silence),
        ]
        if capture_wav is not None:
            args += ["-WavPath", str(capture_wav)]
        try:
            self._run_powershell(
                self._listen_script,
                args,
                timeout=float(initial_timeout) + 60.0,
            )
            if out_file.exists():
                return out_file.read_text(encoding="utf-8").strip()
            return ""
        finally:
            out_file.unlink(missing_ok=True)

    @staticmethod
    def _run_powershell(
        script: Path,
        args: list[str],
        *,
        timeout: float,
    ) -> None:
        """Run a PowerShell helper script.

        Args:
            script: Path to the .ps1 helper.
            args: Script arguments.
            timeout: Subprocess timeout in seconds.

        Raises:
            WindowsSpeechError: When PowerShell exits with an error.
        """
        completed = subprocess.run(  # noqa: S603
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                *args,
            ],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            msg = f"Windows speech command failed: {detail or 'unknown error'}"
            raise WindowsSpeechError(msg)
