# Voice Integration — Jarvis OS Sprint 8

> Talk to Jarvis with your microphone and hear spoken replies.

---

## Overview

Sprint 8 adds **real-time voice interaction** over WebSocket:

```
Mic audio → STT → ChatService → TTS → audio playback
```

| Component | Role |
|-----------|------|
| **SpeechToText** port | Transcribe user speech |
| **TextToSpeech** port | Synthesize assistant reply |
| **VoiceService** | Orchestrates STT → chat → TTS |
| **WebSocket** `/api/v1/voice/ws` | Streaming voice session |

Voice sessions can reuse an existing `conversation_id` so spoken turns stay in the same chat thread as text messages.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_ENABLED` | `true` | Enable voice WebSocket endpoint |
| `VOICE_STT_PROVIDER` | `openai` | STT adapter: `openai` (Whisper) or `stub` (tests) |
| `VOICE_TTS_PROVIDER` | `edge` | TTS adapter: `edge`, `openai`, or `stub` |
| `OPENAI_WHISPER_MODEL` | `whisper-1` | Whisper model name |
| `OPENAI_TTS_MODEL` | `tts-1` | OpenAI TTS model |
| `OPENAI_TTS_VOICE` | `alloy` | OpenAI TTS voice |
| `EDGE_TTS_VOICE` | `en-US-GuyNeural` | Edge TTS voice (no API key) |

### API keys

- **Chat (LLM):** Uses your configured LLM provider (e.g. OpenRouter via `OPENROUTER_API_KEY`).
- **Whisper STT:** Requires a **direct OpenAI** key in `OPENAI_API_KEY`. OpenRouter keys (`sk-or-*`) are ignored for Whisper.
- **Edge TTS:** Free — no API key required (default).
- **OpenAI TTS:** Uses the same direct OpenAI key as Whisper.

For local development without a direct OpenAI key, set `VOICE_STT_PROVIDER=stub` or add a separate OpenAI key for voice only.

---

## WebSocket protocol

Connect to **`ws://localhost:8000/api/v1/voice/ws`**.

### Handshake

Server sends:

```json
{
  "type": "ready",
  "voice_enabled": true,
  "stt_provider": "openai_whisper",
  "tts_provider": "edge"
}
```

When `voice_enabled` is `false`, STT/TTS are misconfigured or `VOICE_ENABLED=false`. Text chat at `POST /api/v1/chat` still works.

### Client → server

| Message | Fields | Purpose |
|---------|--------|---------|
| `config` | `conversation_id?`, `enable_tools?`, `confirm?` | Session options |
| `audio` | `data` (base64), `format` | Audio chunk (wav, webm, mp3, …) |
| `end_turn` | — | Signal end of user speech |

### Server → client

| Message | Fields | Purpose |
|---------|--------|---------|
| `transcript` | `text` | STT result |
| `response` | `text`, `conversation_id` | Assistant reply |
| `audio_out` | `data` (base64), `format` | Synthesized speech |
| `error` | `message`, `code` | Error details |

### Example flow

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/voice/ws");

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === "ready") console.log("Voice ready", msg);
  if (msg.type === "transcript") console.log("You said:", msg.text);
  if (msg.type === "response") console.log("Jarvis:", msg.text);
  if (msg.type === "audio_out") playAudio(msg.data, msg.format);
};

ws.onopen = () => {
  ws.send(JSON.stringify({ type: "config", conversation_id: null }));
  ws.send(JSON.stringify({
    type: "audio",
    data: base64Audio,
    format: "webm",
  }));
  ws.send(JSON.stringify({ type: "end_turn" }));
};
```

---

## Architecture

```
app/voice/
├── interfaces/          # SpeechToText, TextToSpeech ports
├── adapters/
│   ├── openai_whisper.py
│   ├── openai_tts.py
│   ├── edge_tts.py
│   └── stub_*.py        # Test doubles
├── factory.py           # build_speech_to_text / build_text_to_speech
├── session_handler.py   # WebSocket protocol loop
└── schemas/             # Protocol + result models

app/services/voice.py      # VoiceService (STT → ChatService → TTS)
app/api/routes/voice.py    # WebSocket route
```

---

## Testing

Tests use stub STT/TTS providers (configured in `tests/conftest.py`):

```bash
pytest tests/voice/ tests/test_voice_websocket.py -v
```

---

## Fallback to text chat

When voice is unavailable, clients should continue using **`POST /api/v1/chat`**. The WebSocket `ready` message reports `voice_enabled: false` so UIs can hide or disable the mic button (Sprint 9).
