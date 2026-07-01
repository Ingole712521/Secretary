# Jarvis OS — Full Path D

> **Goal:** A Jarvis you can talk to that remembers context and can control your PC.  
> **Sequence:** A (Conversation) → B (PC Control) → C (Voice)

---

## Current State

| Layer | Status |
|-------|--------|
| Core API + DI | Done |
| Brain (orchestrator, planner, context) | Done (planning only) |
| Tool platform framework | Done (no concrete tools) |
| OpenRouter chat | Done (single-turn text) |

---

## Sprint 4 — Conversational Jarvis (A)

**Goal:** Multi-turn chat with session memory. Jarvis remembers the thread.

### Deliverables

- [x] `conversation_id` on chat request/response
- [x] Full message history sent to LLM on each turn
- [x] User + assistant messages persisted in `ConversationManager`
- [x] Default Jarvis system prompt via `JARVIS_SYSTEM_PROMPT`
- [x] `GET /api/v1/conversations` — list sessions
- [x] `GET /api/v1/conversations/{id}` — session detail
- [ ] Long-term semantic memory (facts, embeddings) — deferred to Sprint 7

### Acceptance

- Second message in same `conversation_id` includes prior context
- Unknown `conversation_id` returns 404
- Conversations listable via API

---

## Sprint 5 — PC Control (B.1)

**Goal:** Jarvis can run terminal commands on your PC.

### Deliverables

- [ ] OpenRouter tool/function calling support in `LLMRequest` / `LLMResponse`
- [ ] `TerminalTool` — execute shell commands (Windows PowerShell primary)
- [ ] `ToolAwareChatService` or extend `ChatService` with tool loop
- [ ] Register terminal tool at startup
- [ ] Confirmation policy for destructive commands
- [ ] `POST /api/v1/chat` returns tool execution metadata when tools run

### Acceptance

- "List files in my Downloads folder" triggers terminal tool
- Dangerous commands require `confirm: true` in request
- Tool results fed back to LLM for final reply

---

## Sprint 6 — Desktop Automation (B.2)

**Goal:** Jarvis can interact with your desktop (windows, mouse, keyboard).

### Deliverables

- [ ] `DesktopAutomation` port + Windows adapter
- [ ] Tools: `focus_window`, `click`, `type_text`, `screenshot_region`
- [ ] Register desktop tools in tool platform
- [ ] Wire into chat tool loop

### Acceptance

- "Open Notepad and type hello" works on Windows
- Unsupported actions return clear errors
- High-risk actions gated by security policy

---

## Sprint 7 — Long-Term Memory (A.2)

**Goal:** Jarvis remembers facts about you across sessions.

### Deliverables

- [ ] `MemoryStore` port + file/SQLite adapter
- [ ] Store and retrieve facts ("My name is Nehal")
- [ ] Inject relevant memories into chat context
- [ ] `POST /api/v1/memory`, `GET /api/v1/memory/search`

---

## Sprint 8 — Voice (C)

**Goal:** Talk to Jarvis with microphone and hear replies.

### Deliverables

- [ ] `SpeechToText` / `TextToSpeech` ports
- [ ] Whisper or OpenRouter audio STT adapter
- [ ] TTS adapter (OpenAI TTS or local)
- [ ] `WebSocket /api/v1/voice` — streaming audio session
- [ ] Voice session linked to `conversation_id`

### Acceptance

- Speak → transcript → Jarvis reply → audio playback
- Falls back to text chat when voice unavailable

---

## Sprint 9 — Chat UI

**Goal:** Desktop-friendly interface (not just Swagger).

### Deliverables

- [ ] Simple web UI at `/` or `/chat`
- [ ] Message history panel
- [ ] Mic button (when Sprint 8 complete)
- [ ] Tool action log visible to user

---

## Sprint 10 — Autonomous Agent (D finale)

**Goal:** Multi-step tasks without micromanaging each step.

### Deliverables

- [ ] Wire `Orchestrator` to LLM + tools + planner
- [ ] Agent loop: plan → execute tools → report
- [ ] `require_plan: true` on execution endpoint
- [ ] Audit log for all tool invocations

---

## Architecture (Target)

```
User (voice or text)
        │
        ▼
   Chat / Voice API
        │
        ▼
   ChatService (+ tool loop)
        │
   ┌────┴────┬────────────┬──────────┐
   ▼         ▼            ▼          ▼
Conversation Memory   ModelRouter  ToolExecutor
 Manager   Store                         │
   │                              Terminal
   │                              Desktop
   ▼                              Browser…
 OpenRouter LLM
```

---

## How to Follow Along

| Sprint | Doc to read after completion |
|--------|------------------------------|
| 4 | This file + test with `conversation_id` |
| 5 | `TERMINAL_TOOLS.md` (to be created) |
| 6 | `DESKTOP_AUTOMATION.md` (to be created) |
| 8 | `VOICE_INTEGRATION.md` (to be created) |

**Next up:** Sprint 5 — say **"start sprint 5"** when ready for PC control.
