"""Terminal voice assistant for Jarvis.

Run this to talk to Jarvis by voice:

    python voice_cli.py

Jarvis greets you, then listens on your microphone and acts on what you say
(opening apps, projects, running commands, answering questions) using the
same chat + tools pipeline as the web UI. Speech works fully offline through
the built-in Windows speech engine.

Say "stop", "exit", "quit", or "goodbye" to end the session.
"""

from __future__ import annotations

import asyncio
import os

from app.config.settings import get_settings
from app.dependencies.container import build_container
from app.models.chat import ChatRequest
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


async def run() -> None:
    """Run the greet -> listen -> act -> speak loop."""
    settings = get_settings()
    if not settings.has_llm_credentials:
        print(
            "No LLM API key configured. Set OPENROUTER_API_KEY in .env first.",
        )
        return

    try:
        speech = WindowsSpeech()
    except WindowsSpeechError as exc:
        print(f"Voice unavailable: {exc}")
        return

    container = build_container(settings)
    user_name = os.getenv("JARVIS_USER_NAME", "Nehal")
    conversation_id: str | None = None

    greeting = f"Hello {user_name}. How are you? I'm listening."
    print(f"\nJarvis: {greeting}")
    speech.speak(greeting)

    print("\n(Say 'stop' or 'goodbye' to exit. Press Ctrl+C to quit.)\n")

    while True:
        print("Listening...")
        try:
            heard = speech.listen()
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
            speech.speak(farewell)
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
        speech.speak(reply)


def main() -> None:
    """Entry point with graceful Ctrl+C handling."""
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
