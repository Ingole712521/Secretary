"""Quick microphone + transcription check.

Run this to verify Jarvis can hear you clearly:

    python mic_test.py

The mic level meter appears while recording. After you speak, it prints
capture stats and what Google / Windows each transcribed.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from app.voice.google_speech import GoogleSpeechError, GoogleSpeechRecognizer
from app.voice.mic_recorder import MicRecorder
from app.voice.windows_speech import WindowsSpeech


def main() -> None:
    """Record one phrase and show capture stats plus transcriptions."""
    recorder = MicRecorder()
    wav = Path(tempfile.gettempdir()) / "jarvis_voice" / f"mt_{uuid.uuid4().hex}.wav"

    print("\nMic level meter will appear. Speak clearly when the bar moves...")
    result = recorder.record(wav, show_meter=True)

    print(f"\nCapture stats:")
    print(f"  max level (RMS) : {result.max_rms:.0f}")
    print(f"  speech detected : {result.speech_detected}")
    print(f"  audio captured  : {result.captured} ({result.bytes_written} bytes)")

    if not result.captured:
        print(
            "\nNo usable audio captured.\n"
            "Fix: Windows Settings -> System -> Sound -> Input -> "
            "choose your mic and set volume to 80-100%.\n"
            "Then run this test again.",
        )
        wav.unlink(missing_ok=True)
        return

    size_kb = wav.stat().st_size / 1024
    print(f"  file size       : {size_kb:.1f} KB\n")

    lang = os.getenv("JARVIS_STT_LANGUAGE", "en-IN")
    try:
        google = GoogleSpeechRecognizer(language=lang)
        heard = google.transcribe(wav)
        print(f"Google heard ({lang}): {heard!r}")
    except GoogleSpeechError as exc:
        print(f"Google failed: {exc}")

    try:
        print(f"Windows heard       : {WindowsSpeech().transcribe_wav(wav)!r}")
    except Exception as exc:  # noqa: BLE001
        print(f"Windows failed: {exc}")

    wav.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
