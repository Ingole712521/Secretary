"""Terminal voice assistant for Jarvis.

Run this to talk to Jarvis by voice:

    python voice_cli.py

Jarvis greets you, then listens on your microphone and acts on what you say
(opening apps, projects, running commands, answering questions) using the
same chat + tools pipeline as the web UI.

Listening: the Windows engine detects and records your phrase, and Google's
free speech service transcribes it for high accuracy (falls back to the
offline Windows transcription when there is no internet).

Speaking: a smooth neural voice (Edge TTS), falling back to the offline
Windows voice when there is no internet connection.

Environment variables:
    JARVIS_NEURAL_VOICE  Edge neural voice name (default en-US-JennyNeural).
    JARVIS_VOICE         Offline fallback voice: "female" or "male".
    JARVIS_STT_LANGUAGE  Recognition language, e.g. en-US or en-IN.
    JARVIS_USER_NAME     Name Jarvis greets you by (default Nehal).

Say "stop", "exit", "quit", or "goodbye" to end the session.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from pathlib import Path

from app.config.settings import get_settings
from app.dependencies.container import build_container
from app.models.chat import ChatRequest
from app.voice.edge_speech import EdgeSpeaker, EdgeSpeechError
from app.voice.google_speech import GoogleSpeechError, GoogleSpeechRecognizer
from app.voice.windows_speech import WindowsSpeech, WindowsSpeechError

EXIT_PHRASES = {
    "stop",
    "exit",
    "quit",
    "goodbye",
    "good bye",
    "bye",
    "shutdown",
    "shut down",
    "that's all",
    "thats all",
}


def _is_exit(text: str) -> bool:
    """Return True when the user asked to end the session."""
    normalized = text.strip().lower().rstrip(".!?")
    return normalized in EXIT_PHRASES


def _tmp_wav() -> Path:
    """Return a fresh temp WAV path for one captured utterance."""
    work = Path(tempfile.gettempdir()) / "jarvis_voice"
    work.mkdir(parents=True, exist_ok=True)
    return work / f"cap_{uuid.uuid4().hex}.wav"


async def run() -> None:
    """Run the greet -> listen -> act -> speak loop."""
    settings = get_settings()
    if not settings.has_llm_credentials:
        print(
            "No LLM API key configured. Set OPENROUTER_API_KEY in .env first.",
        )
        return

    try:
        speech = WindowsSpeech(voice=os.getenv("JARVIS_VOICE", "female"))
    except WindowsSpeechError as exc:
        print(f"Voice unavailable: {exc}")
        return

    # Prefer a smooth neural voice; fall back to the built-in voice offline.
    neural: EdgeSpeaker | None = None
    neural_ok = True
    try:
        neural = EdgeSpeaker(
            voice=os.getenv("JARVIS_NEURAL_VOICE", "en-US-JennyNeural"),
        )
    except Exception:  # noqa: BLE001
        neural = None

    async def say(text: str) -> None:
        """Speak text with the neural voice, falling back to SAPI."""
        nonlocal neural_ok
        if neural is not None and neural_ok:
            try:
                await neural.speak(text)
                return
            except EdgeSpeechError:
                # Offline or playback issue: use the offline voice from now on.
                neural_ok = False
        speech.speak(text)

    # High-accuracy transcription (Google) on top of the Windows recorder.
    google_stt: GoogleSpeechRecognizer | None = None
    google_ok = True
    try:
        google_stt = GoogleSpeechRecognizer(
            language=os.getenv("JARVIS_STT_LANGUAGE", "en-US"),
        )
    except Exception:  # noqa: BLE001
        google_stt = None

    def hear() -> str:
        """Capture one phrase, transcribing with Google when possible."""
        nonlocal google_ok
        wav = _tmp_wav() if google_stt is not None and google_ok else None
        sapi_text = speech.listen(capture_wav=wav)
        if wav is None:
            return sapi_text
        try:
            if wav.exists() and wav.stat().st_size > 0 and google_stt is not None:
                accurate = google_stt.transcribe(wav)
                if accurate:
                    return accurate
        except GoogleSpeechError:
            # Offline or endpoint issue: stick with the offline engine.
            google_ok = False
        finally:
            wav.unlink(missing_ok=True)
        return sapi_text

    container = build_container(settings)
    user_name = os.getenv("JARVIS_USER_NAME", "Nehal")
    conversation_id: str | None = None

    greeting = f"Hello {user_name}. How are you? I'm listening."
    print(f"\nJarvis: {greeting}")
    await say(greeting)

    print("\n(Say 'stop' or 'goodbye' to exit. Press Ctrl+C to quit.)\n")

    while True:
        print("Listening...")
        try:
            heard = hear()
        except WindowsSpeechError as exc:
            print(f"  (listen error: {exc})")
            continue

        if not heard:
            # Nothing recognized within the timeout; keep listening.
            continue

        print(f"You: {heard}")

        if _is_exit(heard):
            farewell = f"Goodbye {user_name}."
            print(f"Jarvis: {farewell}")
            await say(farewell)
            break

        try:
            response = await container.chat_service.chat(
                ChatRequest(
                    message=heard,
                    conversation_id=conversation_id,
                    enable_tools=True,
                    confirm=True,
                ),
            )
            conversation_id = response.conversation_id
            reply = response.message or "Done."
        except Exception as exc:  # noqa: BLE001
            reply = f"Sorry, something went wrong: {exc}"

        print(f"Jarvis: {reply}\n")
        await say(reply)


def main() -> None:
    """Entry point with graceful Ctrl+C handling."""
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
