# Free Voice Agent — Quick Start

Jarvis OS includes a **100% free voice agent** stack:

| Component | Technology | Cost |
|-----------|------------|------|
| **Speech input** | Browser Web Speech API (Chrome/Edge) | Free |
| **Brain** | OpenRouter `openrouter/auto` | Free tier / your existing key |
| **Speech output** | Microsoft Edge TTS | Free |
| **Task execution** | Terminal + desktop tools | Free (local) |

## Run

```bash
cd "D:\New folder\Secratory"
python main.py
```

Open in your browser:

**http://127.0.0.1:8000**

## How to use

1. Allow microphone permission when prompted.
2. Click the **mic** button and speak (e.g. *"Hey Jarvis, what can you do?"*).
3. Or type a message and press **Send**.
4. Enable **PC tools** to let Jarvis run terminal/desktop commands.
5. Jarvis will **speak replies** automatically (Edge TTS).

## Example tasks

- *"Hello Jarvis, my name is Nehal"*
- *"What's in my current folder?"* (with tools enabled)
- *"Open my React Native project"* (with tools enabled)

## Configuration (`.env`)

```env
LLM_PROVIDER=openrouter
OPENROUTER_MODEL=openrouter/auto
VOICE_TTS_PROVIDER=edge
EDGE_TTS_VOICE=en-US-GuyNeural
TOOLS_ENABLED=true
```

Your OpenRouter key is read from `OPENAI_API_KEY` when it starts with `sk-or-`.

## API endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Voice chat UI |
| `POST /api/v1/chat` | Text/voice brain |
| `POST /api/v1/voice/synthesize` | Free TTS audio |
| `WS /api/v1/voice/ws` | Full voice WebSocket |

## Troubleshooting

- **Mic not working**: Use Chrome or Edge; Firefox has limited Web Speech API support.
- **Chat errors**: Ensure `LLM_PROVIDER=openrouter` and a valid `sk-or-*` key.
- **Tools fail**: Run the server from an elevated terminal if commands need admin access.
