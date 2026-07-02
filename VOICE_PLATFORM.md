# Voice Platform — Jarvis OS

> Modular, interface-driven voice interaction: wake word → speech → Jarvis reply → spoken response.

---

## Architecture

```
Microphone
    ↓
Wake Word ("hey jarvis")
    ↓
Voice Activity Detection (VAD)
    ↓
Speech To Text (Faster Whisper default)
    ↓
Conversation Controller → ChatService → OpenRouter
    ↓
Text To Speech (Piper default)
    ↓
Audio Output (Speaker)
```

A parallel **WebSocket path** (`/api/v1/voice/ws`) supports browser/client audio without local microphone hardware.

---

## Module Responsibilities

| Module | Path | Responsibility |
|--------|------|----------------|
| **Voice Manager** | `app/voice/manager/` | Lifecycle: start, stop, pause, resume, shutdown; orchestrates pipeline |
| **Microphone** | `app/voice/microphone/` | Audio capture, device selection, buffering |
| **Wake Word** | `app/voice/providers/wakeword/` | Detect "hey jarvis" (openWakeWord, Porcupine-ready interfaces) |
| **VAD** | `app/voice/providers/vad/` | End-of-speech detection (Silero, manual, WebRTC-ready) |
| **STT** | `app/voice/providers/stt/` | Speech-to-text (Faster Whisper, OpenAI Whisper, stubs) |
| **TTS** | `app/voice/providers/tts/` | Text-to-speech (Piper, Edge, OpenAI, stubs) |
| **Conversation** | `app/voice/conversation/` | Transcript → ChatService → synthesis |
| **Audio Output** | `app/voice/audio/` | Playback, queueing, interrupt, volume |
| **Events** | `app/voice/events/` | Pub/sub voice lifecycle events |
| **Interfaces** | `app/voice/interfaces/` | Replaceable ports (Protocols) |
| **Factory** | `app/voice/factory.py` | Dependency wiring from settings |

All implementations depend on **interfaces**, not concrete providers. Swap providers via environment variables without code changes.

---

## Voice Flow

### Local voice (Voice Manager)

1. `POST /api/v1/voice/start` — starts wake word listening
2. User says **"Hey Jarvis"** → `WakeWordDetected` event
3. Microphone captures speech until VAD detects silence
4. STT transcribes audio → `SpeechRecognized` event
5. Conversation Controller calls `ChatService.chat()` → OpenRouter
6. TTS synthesizes reply → speaker plays audio
7. Manager returns to listening for next wake word

### WebSocket voice (remote client)

1. Connect to `ws://localhost:8000/api/v1/voice/ws`
2. Send `config` → `audio` chunks → `end_turn`
3. Server returns `transcript`, `response`, `audio_out`

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `VOICE_ENABLED` | `true` | Master voice switch |
| `VOICE_STT_PROVIDER` | `faster_whisper` | `faster_whisper`, `openai`, `stub` |
| `VOICE_TTS_PROVIDER` | `piper` | `piper`, `edge`, `openai`, `stub` |
| `VOICE_VAD_PROVIDER` | `manual` | `silero`, `manual`, `stub` |
| `VOICE_WAKEWORD_PROVIDER` | `stub` | `openwakeword`, `stub` |
| `VOICE_MICROPHONE_PROVIDER` | `stub` | `sounddevice`, `stub` |
| `VOICE_AUDIO_OUTPUT_PROVIDER` | `stub` | `sounddevice` (queue player), `stub` |
| `VOICE_WAKE_WORD` | `hey jarvis` | Wake phrase |
| `VOICE_LANGUAGE` | `en` | Default STT language |
| `VOICE_SAMPLE_RATE` | `16000` | Capture sample rate |
| `VOICE_SILENCE_TIMEOUT_MS` | `800` | End-of-speech silence |
| `VOICE_WHISPER_MODEL` | `base` | Faster Whisper model size |
| `VOICE_WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `VOICE_WHISPER_COMPUTE_TYPE` | `int8` | Faster Whisper compute type |
| `VOICE_PIPER_VOICE` | `data/voices/...onnx` | Piper voice model path |
| `VOICE_PIPER_SPEED` | `1.0` | Speech speed |
| `VOICE_PIPER_PITCH` | `1.0` | Pitch multiplier |
| `VOICE_PIPER_VOLUME` | `1.0` | Volume multiplier |
| `VOICE_MICROPHONE_DEVICE` | — | Device index or name |
| `VOICE_SPEAKER_DEVICE` | — | Output device index or name |

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/voice/start` | Start local voice listening |
| `POST` | `/api/v1/voice/stop` | Stop voice platform |
| `GET` | `/api/v1/voice/status` | Component health and state |
| `WS` | `/api/v1/voice/ws` | Browser/client voice session |

---

## Events

Subscribe via `VoiceEventBus.subscribe()`:

| Event | When |
|-------|------|
| `voice_started` | Voice manager started |
| `voice_stopped` | Voice manager stopped |
| `wake_word_detected` | Wake phrase recognized |
| `speech_detected` | Audio chunk during utterance |
| `speech_recognized` | STT complete |
| `llm_request_started` | Chat request sent |
| `llm_response_received` | Assistant reply received |
| `speech_playing` | TTS playback started |
| `speech_finished` | Playback complete |
| `error_occurred` | Pipeline error |

---

## Provider System

Providers are selected in `app/voice/factory.py` from settings. Each module implements a **Protocol** in `app/voice/interfaces/`.

### Implemented providers

| Type | Providers |
|------|-----------|
| STT | Faster Whisper, OpenAI Whisper, Stub |
| TTS | Piper, Edge TTS, OpenAI TTS, Stub |
| VAD | Silero, Manual (energy), Stub |
| Wake Word | openWakeWord, Stub |
| Microphone | sounddevice, Stub |
| Audio | Queue player (sounddevice), Stub |

### Future expansion

Interfaces are ready for: Deepgram, Google STT, Azure STT, ElevenLabs, Azure TTS, Porcupine, WebRTC VAD. Register new providers in `factory.py` or `providers/registry.py`.

---

## Production setup

```env
VOICE_ENABLED=true
VOICE_STT_PROVIDER=faster_whisper
VOICE_TTS_PROVIDER=piper
VOICE_VAD_PROVIDER=silero
VOICE_WAKEWORD_PROVIDER=openwakeword
VOICE_MICROPHONE_PROVIDER=sounddevice
VOICE_AUDIO_OUTPUT_PROVIDER=sounddevice
VOICE_WAKE_WORD=hey jarvis
VOICE_WHISPER_MODEL=base
VOICE_PIPER_VOICE=data/voices/en_US-lessac-medium.onnx
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-...
```

Install voice dependencies:

```bash
pip install faster-whisper piper-tts sounddevice numpy openwakeword edge-tts
```

Download a Piper voice model to `data/voices/`.

---

## Testing

Tests use stub providers (configured in `tests/conftest.py`):

```bash
pytest tests/voice/ -v
```

---

## Dependency injection

```python
# app/dependencies/container.py
voice_platform = build_voice_platform(settings, chat_service)
voice_platform_service = VoicePlatformService(settings, voice_platform)
```

Access in routes via `VoicePlatformServiceDep` or `VoiceServiceDep` (WebSocket).

---

## Design principles

- **SOLID** — each module has a single responsibility
- **Interface-driven** — no tight coupling to Faster Whisper, Piper, etc.
- **Replaceable** — swap providers via config
- **Event-driven** — UI and plugins can subscribe to `VoiceEventBus`
- **Tool-ready** — conversation controller passes `enable_tools` to ChatService for future PC control via voice
