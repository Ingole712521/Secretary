"""Direct microphone recorder with voice-activity detection.

Records the default microphone to a clean 16 kHz mono PCM WAV using the
native Windows ``winmm`` API (no PyAudio / native Python deps required).
Audio is captured from the moment listening starts (not gated on VAD),
then trimmed on silence after speech is detected.
"""

from __future__ import annotations

import platform
import subprocess
import tempfile
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.voice.mic_level import MicLevelDisplay, poll_level_file

# C# recorder compiled on the fly by PowerShell. Uses waveIn* from winmm.
_RECORDER_PS = r"""param(
    [string]$Path,
    [int]$SampleRate = 16000,
    [int]$InitialTimeoutMs = 15000,
    [int]$EndSilenceMs = 1200,
    [double]$Threshold = -1,
    [string]$LevelPath = "",
    [string]$ResultPath = ""
)
$ErrorActionPreference = 'Stop'
$code = @'
using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Globalization;

public static class MicRecorder
{
    [StructLayout(LayoutKind.Sequential)]
    struct WAVEFORMATEX {
        public ushort wFormatTag; public ushort nChannels; public uint nSamplesPerSec;
        public uint nAvgBytesPerSec; public ushort nBlockAlign; public ushort wBitsPerSample;
        public ushort cbSize;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct WAVEHDR {
        public IntPtr lpData; public uint dwBufferLength; public uint dwBytesRecorded;
        public IntPtr dwUser; public uint dwFlags; public uint dwLoops;
        public IntPtr lpNext; public IntPtr reserved;
    }
    [DllImport("winmm.dll")] static extern int waveInOpen(out IntPtr h, uint id, ref WAVEFORMATEX f, IntPtr cb, IntPtr inst, uint flags);
    [DllImport("winmm.dll")] static extern int waveInClose(IntPtr h);
    [DllImport("winmm.dll")] static extern int waveInPrepareHeader(IntPtr h, IntPtr p, uint cb);
    [DllImport("winmm.dll")] static extern int waveInUnprepareHeader(IntPtr h, IntPtr p, uint cb);
    [DllImport("winmm.dll")] static extern int waveInAddBuffer(IntPtr h, IntPtr p, uint cb);
    [DllImport("winmm.dll")] static extern int waveInStart(IntPtr h);
    [DllImport("winmm.dll")] static extern int waveInStop(IntPtr h);
    [DllImport("winmm.dll")] static extern int waveInReset(IntPtr h);

    const uint WAVE_MAPPER = 0xFFFFFFFF;
    const uint WHDR_DONE = 0x00000001;

    public static void Record(string path, int sampleRate, int initialTimeoutMs, int endSilenceMs, double threshold, string levelPath, string resultPath)
    {
        int channels = 1, bits = 16;
        WAVEFORMATEX fmt = new WAVEFORMATEX();
        fmt.wFormatTag = 1; fmt.nChannels = (ushort)channels;
        fmt.nSamplesPerSec = (uint)sampleRate; fmt.wBitsPerSample = (ushort)bits;
        fmt.nBlockAlign = (ushort)(channels * bits / 8);
        fmt.nAvgBytesPerSec = (uint)(sampleRate * fmt.nBlockAlign); fmt.cbSize = 0;

        IntPtr h;
        int rc = waveInOpen(out h, WAVE_MAPPER, ref fmt, IntPtr.Zero, IntPtr.Zero, 0);
        if (rc != 0) throw new Exception("waveInOpen failed: " + rc);

        int bufCount = 8, frameMs = 80;
        int bufBytes = sampleRate * frameMs / 1000 * fmt.nBlockAlign;
        int hdrSize = Marshal.SizeOf(typeof(WAVEHDR));
        IntPtr[] pHdr = new IntPtr[bufCount];
        IntPtr[] pData = new IntPtr[bufCount];
        for (int i = 0; i < bufCount; i++) {
            pData[i] = Marshal.AllocHGlobal(bufBytes);
            WAVEHDR hd = new WAVEHDR();
            hd.lpData = pData[i]; hd.dwBufferLength = (uint)bufBytes;
            pHdr[i] = Marshal.AllocHGlobal(hdrSize);
            Marshal.StructureToPtr(hd, pHdr[i], false);
            waveInPrepareHeader(h, pHdr[i], (uint)hdrSize);
            waveInAddBuffer(h, pHdr[i], (uint)hdrSize);
        }
        waveInStart(h);

        List<byte> pcm = new List<byte>();
        var sw = System.Diagnostics.Stopwatch.StartNew();
        bool started = false; int silenceMs = 0;
        double ambient = 0; int ambientCount = 0; double thr = threshold;
        double maxRms = 0;
        int idx = 0; byte[] tmp = new byte[bufBytes];

        while (true) {
            if (!started && sw.ElapsedMilliseconds > initialTimeoutMs) break;
            if (started && sw.ElapsedMilliseconds > initialTimeoutMs + 45000) break;
            WAVEHDR hd = (WAVEHDR)Marshal.PtrToStructure(pHdr[idx], typeof(WAVEHDR));
            if ((hd.dwFlags & WHDR_DONE) == 0) { Thread.Sleep(5); continue; }
            int n = (int)hd.dwBytesRecorded;
            if (n > 0) {
                Marshal.Copy(hd.lpData, tmp, 0, n);
                // Always capture audio from the start (do not gate on VAD).
                for (int b = 0; b < n; b++) pcm.Add(tmp[b]);

                double sum = 0; int samples = n / 2;
                for (int s = 0; s + 1 < n; s += 2) {
                    short v = (short)(tmp[s] | (tmp[s + 1] << 8));
                    sum += (double)v * v;
                }
                double rms = samples > 0 ? Math.Sqrt(sum / samples) : 0;
                if (rms > maxRms) maxRms = rms;

                // Auto-calibrate a low threshold from early ambient noise.
                if (thr < 0 && ambientCount < 12) {
                    ambient += rms; ambientCount++;
                    if (ambientCount == 12) {
                        double avg = ambient / 12.0;
                        thr = Math.Max(avg * 1.35 + 20, 45);
                    }
                }
                double effThr = thr < 0 ? 60 : thr;
                bool voiced = rms > effThr;
                if (voiced) { started = true; silenceMs = 0; }
                else if (started) { silenceMs += frameMs; }

                if (!string.IsNullOrEmpty(levelPath)) {
                    try {
                        File.WriteAllText(levelPath,
                            string.Format(CultureInfo.InvariantCulture,
                                "{0}|{1}|{2}|{3}", rms, started ? 1 : 0, silenceMs, effThr));
                    } catch {}
                }
                if (started && silenceMs >= endSilenceMs) break;
            }
            hd.dwFlags = 0; hd.dwBytesRecorded = 0;
            Marshal.StructureToPtr(hd, pHdr[idx], false);
            waveInAddBuffer(h, pHdr[idx], (uint)hdrSize);
            idx = (idx + 1) % bufCount;
        }

        waveInStop(h); waveInReset(h);
        for (int i = 0; i < bufCount; i++) {
            waveInUnprepareHeader(h, pHdr[i], (uint)hdrSize);
            Marshal.FreeHGlobal(pData[i]); Marshal.FreeHGlobal(pHdr[i]);
        }
        waveInClose(h);

        byte[] data = NormalizePcm(pcm.ToArray());
        WriteWav(path, data, sampleRate, channels, bits);

        if (!string.IsNullOrEmpty(resultPath)) {
            try {
                File.WriteAllText(resultPath,
                    string.Format(CultureInfo.InvariantCulture,
                        "{0}|{1}|{2}", maxRms, started ? 1 : 0, data.Length));
            } catch {}
        }
        if (!string.IsNullOrEmpty(levelPath)) {
            try { File.Delete(levelPath); } catch {}
        }
    }

    static byte[] NormalizePcm(byte[] data) {
        if (data.Length < 4) return data;
        short maxPeak = 0;
        for (int i = 0; i + 1 < data.Length; i += 2) {
            short v = (short)(data[i] | (data[i + 1] << 8));
            short av = (short)Math.Abs(v);
            if (av > maxPeak) maxPeak = av;
        }
        if (maxPeak >= 800) return data;
        double gain = 10000.0 / Math.Max((int)maxPeak, 1);
        if (gain > 30) gain = 30;
        if (gain <= 1.0) return data;
        byte[] outp = new byte[data.Length];
        for (int i = 0; i + 1 < data.Length; i += 2) {
            short v = (short)(data[i] | (data[i + 1] << 8));
            int amp = (int)(v * gain);
            if (amp > 32767) amp = 32767;
            if (amp < -32768) amp = -32768;
            short s = (short)amp;
            outp[i] = (byte)(s & 0xFF);
            outp[i + 1] = (byte)((s >> 8) & 0xFF);
        }
        return outp;
    }

    static void WriteWav(string path, byte[] data, int sampleRate, int channels, int bits) {
        using (var fs = new FileStream(path, FileMode.Create))
        using (var bw = new BinaryWriter(fs)) {
            int byteRate = sampleRate * channels * bits / 8;
            short blockAlign = (short)(channels * bits / 8);
            bw.Write(Encoding.ASCII.GetBytes("RIFF"));
            bw.Write(36 + data.Length);
            bw.Write(Encoding.ASCII.GetBytes("WAVE"));
            bw.Write(Encoding.ASCII.GetBytes("fmt "));
            bw.Write(16); bw.Write((short)1); bw.Write((short)channels);
            bw.Write(sampleRate); bw.Write(byteRate); bw.Write(blockAlign);
            bw.Write((short)bits);
            bw.Write(Encoding.ASCII.GetBytes("data"));
            bw.Write(data.Length); bw.Write(data);
        }
    }
}
'@
Add-Type -TypeDefinition $code -Language CSharp
[MicRecorder]::Record($Path, $SampleRate, $InitialTimeoutMs, $EndSilenceMs, $Threshold, $LevelPath, $ResultPath)
"""


@dataclass(frozen=True)
class RecordResult:
    """Outcome of one microphone capture."""

    captured: bool
    max_rms: float = 0.0
    speech_detected: bool = False
    bytes_written: int = 0


class MicRecorderError(RuntimeError):
    """Raised when microphone recording is unavailable or fails."""


class MicRecorder:
    """Record microphone audio to a WAV using voice-activity detection."""

    def __init__(
        self,
        *,
        sample_rate: int = 16000,
        initial_timeout_ms: int = 15000,
        end_silence_ms: int = 1200,
        threshold: float = -1.0,
    ) -> None:
        """Initialize the recorder and materialize the helper script."""
        if platform.system() != "Windows":
            msg = "MicRecorder requires Windows (winmm)."
            raise MicRecorderError(msg)
        self._sample_rate = sample_rate
        self._initial_timeout_ms = initial_timeout_ms
        self._end_silence_ms = end_silence_ms
        self._threshold = threshold
        self._work_dir = Path(tempfile.gettempdir()) / "jarvis_voice"
        self._work_dir.mkdir(parents=True, exist_ok=True)
        self._script = self._work_dir / "record.ps1"
        self._script.write_text(_RECORDER_PS, encoding="utf-8")

    def record(self, wav_path: Path, *, show_meter: bool = True) -> RecordResult:
        """Record a single phrase to ``wav_path``.

        Returns:
            ``RecordResult`` describing whether usable audio was captured.
        """
        level_path = self._work_dir / f"lvl_{uuid.uuid4().hex}.txt"
        result_path = self._work_dir / f"res_{uuid.uuid4().hex}.txt"
        args = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self._script),
            "-Path",
            str(wav_path),
            "-SampleRate",
            str(self._sample_rate),
            "-InitialTimeoutMs",
            str(self._initial_timeout_ms),
            "-EndSilenceMs",
            str(self._end_silence_ms),
            "-Threshold",
            str(self._threshold),
            "-LevelPath",
            str(level_path) if show_meter else "",
            "-ResultPath",
            str(result_path),
        ]

        display = MicLevelDisplay()
        stop_meter = threading.Event()
        meter_thread: threading.Thread | None = None
        proc: subprocess.Popen[bytes] | None = None
        stderr = b""

        if show_meter:

            def _run_meter() -> None:
                poll_level_file(
                    level_path,
                    display,
                    stop_when=stop_meter.is_set,
                )

            meter_thread = threading.Thread(target=_run_meter, daemon=True)
            meter_thread.start()

        try:
            proc = subprocess.Popen(  # noqa: S603
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, stderr = proc.communicate(
                timeout=float(self._initial_timeout_ms) / 1000.0 + 90.0,
            )
        except subprocess.TimeoutExpired as exc:
            if proc is not None:
                proc.kill()
                _, stderr = proc.communicate()
            msg = "Recording timed out."
            raise MicRecorderError(msg) from exc
        finally:
            stop_meter.set()
            if meter_thread is not None:
                meter_thread.join(timeout=1.0)
            display.clear()
            level_path.unlink(missing_ok=True)

        err_text = stderr.decode("utf-8", errors="replace").strip()
        if proc is None or proc.returncode != 0 or "Add-Type" in err_text:
            msg = f"Recording failed: {err_text or 'unknown error'}"
            raise MicRecorderError(msg)

        result = _read_result(result_path)
        result_path.unlink(missing_ok=True)
        return result


def _read_result(result_path: Path) -> RecordResult:
    """Parse the sidecar result file written by the recorder."""
    if not result_path.exists():
        return RecordResult(captured=False)
    try:
        parts = result_path.read_text(encoding="utf-8").strip().split("|")
        max_rms = float(parts[0]) if parts else 0.0
        speech = len(parts) > 1 and parts[1] == "1"
        nbytes = int(parts[2]) if len(parts) > 2 else 0
    except (OSError, ValueError):
        return RecordResult(captured=False)

    # Usable when VAD saw speech, or mic level was clearly above silence.
    min_bytes = 16000 * 2 * 300 // 1000  # ~300 ms mono 16-bit
    captured = (speech or max_rms >= 55) and nbytes >= min_bytes
    return RecordResult(
        captured=captured,
        max_rms=max_rms,
        speech_detected=speech,
        bytes_written=nbytes,
    )
