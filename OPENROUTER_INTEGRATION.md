# OpenRouter Integration — Jarvis OS

> First working AI interaction: OpenRouter chat completions via `POST /api/v1/chat`.

---

## 1. Overview

Jarvis OS now connects to [OpenRouter](https://openrouter.ai/) through a concrete `OpenRouterProvider` adapter that implements the existing `LLMProvider` port. A `ChatService` accepts user messages and returns assistant replies. No memory, tool calling, or streaming is implemented yet.

```
Client
  │
  ▼
POST /api/v1/chat
  │
  ▼
ChatService
  │
  ▼
ModelRouter ──► OpenRouterProvider
  │
  ▼
OpenRouter API  (POST /chat/completions)
```

---

## 2. Configuration

Set these environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | Active provider; set to `openrouter` | `openai` |
| `OPENROUTER_API_KEY` | OpenRouter API key | — |
| `OPENROUTER_MODEL` | Default model ID | `openrouter/auto` |
| `OPENROUTER_API_BASE` | API base URL | `https://openrouter.ai/api/v1` |

**Legacy key support:** If `OPENROUTER_API_KEY` is unset but `OPENAI_API_KEY` starts with `sk-or-`, that key is used for OpenRouter.

Example `.env`:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
```

---

## 3. Architecture

### 3.1 LLM Provider Port

Defined in `app/brain/interfaces/llm_provider.py`:

- `provider_name` — provider identifier
- `list_models()` — fetch available models
- `complete(request)` — chat completion
- `health_check()` — connectivity check

### 3.2 OpenRouter Provider

`app/brain/providers/openrouter.py` implements the port:

- Reads API key via `Settings.get_active_llm_api_key()`
- Reads base URL from `Settings.openrouter_api_base`
- Calls `POST {base}/chat/completions` (OpenAI-compatible format)
- Maps `LLMRequest` / `LLMResponse` schemas
- Logs request metadata (never logs API keys)
- Raises `ConfigurationException`, `LLMCompletionError`, or `LLMProviderError` on failure

### 3.3 Provider Registration

`app/brain/providers/factory.py` registers adapters at startup:

```python
if settings.llm_provider == LLMProviderSetting.OPENROUTER:
    openrouter_provider = OpenRouterProvider(settings)
    model_router.register_provider(LLMProviderName.OPENROUTER, openrouter_provider)
```

The provider instance is stored on `BrainContainer.openrouter_provider` for graceful HTTP client shutdown in the application lifespan.

### 3.4 ChatService

`app/services/chat.py`:

1. Validates LLM credentials are configured
2. Resolves the active provider via `ModelRouter.get_provider()`
3. Selects model metadata (supports arbitrary OpenRouter model IDs)
4. Builds `LLMRequest` with optional system prompt + user message
5. Calls `provider.complete()`
6. Returns `ChatResponse`

### 3.5 Dependency Injection

```
create_app()
  └── build_container()
        ├── build_brain() → ModelRouter + OpenRouterProvider
        └── ChatService(settings, model_router)
```

FastAPI route dependencies:

- `ChatServiceDep` → `get_chat_service()` → `container.chat_service`

---

## 4. API

### `POST /api/v1/chat`

**Request body:**

```json
{
  "message": "Hello Jarvis",
  "system_prompt": "You are a helpful assistant.",
  "model": "anthropic/claude-3.5-sonnet",
  "temperature": 0.7,
  "max_tokens": 1024
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `message` | Yes | User message (1–32,000 chars) |
| `system_prompt` | No | System instruction |
| `model` | No | Override configured default model |
| `temperature` | No | 0.0–2.0 (default 0.7) |
| `max_tokens` | No | Max tokens to generate |

**Response:**

```json
{
  "message": "Hello! How can I help you today?",
  "model": "anthropic/claude-3.5-sonnet",
  "provider": "openrouter",
  "finish_reason": "stop",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 8,
    "total_tokens": 20
  }
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Jarvis"}'
```

---

## 5. Error Handling

| Exception | HTTP | Code | When |
|-----------|------|------|------|
| `ValidationException` | 422 | `VALIDATION_ERROR` | Invalid request body |
| `ConfigurationException` | 500 | `CONFIGURATION_ERROR` | Missing API key |
| `ModelRoutingError` | 500 | `MODEL_ROUTING_ERROR` | Provider not registered |
| `LLMCompletionError` | 502 | `LLM_COMPLETION_ERROR` | OpenRouter HTTP error response |
| `LLMProviderError` | 502 | `LLM_PROVIDER_ERROR` | Network/transport failure |

All errors use the standard `ErrorResponse` envelope with `correlation_id`.

---

## 6. Logging

| Logger | Purpose |
|--------|---------|
| `jarvis.llm` | OpenRouter request/response metadata |
| `jarvis.chat` | ChatService orchestration |
| `jarvis.errors` | Mapped application errors |

API keys are never written to logs.

---

## 7. Testing

Tests use `httpx.MockTransport` to avoid real API calls:

- `tests/brain/test_openrouter_provider.py` — provider unit tests
- `tests/test_chat_api.py` — `POST /api/v1/chat` integration tests

Run:

```bash
python -m pytest tests/brain/test_openrouter_provider.py tests/test_chat_api.py -v
```

---

## 8. What Is Not Implemented

| Feature | Status |
|---------|--------|
| Conversation memory / persistence | Not implemented |
| Tool calling | Not implemented |
| Streaming responses | Not implemented |
| OpenAI / Anthropic direct adapters | Not implemented |
| Brain orchestrator integration | Chat bypasses orchestrator for now |

---

## 9. Adding Another Provider

1. Create `app/brain/providers/<name>.py` implementing `LLMProvider`
2. Register in `app/brain/providers/factory.py`
3. Add settings fields in `app/config/settings.py`
4. Extend `get_active_llm_api_key()` and `get_active_llm_model()`
5. Add unit tests with mocked HTTP transport

The `ChatService` and `POST /api/v1/chat` endpoint require no changes when a new provider is registered for the active `LLM_PROVIDER` setting.

---

## 10. File Reference

| File | Role |
|------|------|
| `app/brain/interfaces/llm_provider.py` | Provider port |
| `app/brain/providers/openrouter.py` | OpenRouter adapter |
| `app/brain/providers/factory.py` | Provider registration |
| `app/services/chat.py` | Chat orchestration |
| `app/models/chat.py` | API request/response models |
| `app/api/routes/chat.py` | HTTP route |
| `app/dependencies/container.py` | DI wiring |
| `app/core/exception_mapping.py` | HTTP status mapping |
| `app/core/lifespan.py` | Provider HTTP client cleanup |
