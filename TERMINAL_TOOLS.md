# Terminal Tools — Jarvis OS Sprint 5

> Jarvis can run shell commands on your PC via LLM tool calling.

---

## Overview

Sprint 5 connects the **chat API**, **OpenRouter tool calling**, and the **tool platform** so Jarvis can execute terminal commands when the model decides it needs to inspect or change your system.

```
User message
     │
     ▼
ChatService
     │
     ▼
ToolLoopService ◄──── OpenRouter (tool_calls)
     │
     ▼
ToolExecutor ──► TerminalTool ──► PowerShell / sh
     │
     ▼
Tool result ──► LLM ──► Final reply + tools_used metadata
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TOOLS_ENABLED` | `true` | Register and expose production tools |
| `TERMINAL_COMMAND_TIMEOUT` | `30` | Max seconds per command |
| `CHAT_MAX_TOOL_ITERATIONS` | `5` | Max tool loop rounds per chat turn |
| `JARVIS_SYSTEM_PROMPT` | (built-in) | Instructs Jarvis it may use the terminal |

---

## Terminal Tool

| Field | Value |
|-------|-------|
| **ID** | `terminal.run` |
| **LLM function name** | `terminal_run` |
| **Shell (Windows)** | PowerShell (`-NoProfile -NonInteractive`) |
| **Shell (Linux/macOS)** | `sh -c` |
| **Permissions** | `execute` |

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `command` | string | Yes | Shell command to run |
| `cwd` | string | No | Working directory |

### Output

```json
{
  "command": "Get-ChildItem",
  "exit_code": 0,
  "stdout": "...",
  "stderr": "",
  "shell": "powershell"
}
```

---

## Chat API Changes

### Request (`POST /api/v1/chat`)

| Field | Default | Description |
|-------|---------|-------------|
| `enable_tools` | `true` | Allow model to invoke tools |
| `confirm` | `false` | Confirm dangerous tool execution |

### Response

| Field | Description |
|-------|-------------|
| `tools_used` | List of tools executed this turn |
| `confirmation_required` | `true` when a dangerous command needs approval |
| `pending_tool_id` | Tool waiting for `confirm=true` |

### Example — safe command

```json
{
  "message": "List files in my Downloads folder"
}
```

Response includes `tools_used` with `terminal.run` and the assistant's summary.

### Example — dangerous command

First request:

```json
{ "message": "Delete the temp folder recursively" }
```

Response:

```json
{
  "confirmation_required": true,
  "pending_tool_id": "terminal.run",
  "message": "This action requires confirmation. Resend your message with confirm=true to proceed."
}
```

Retry with confirmation:

```json
{
  "message": "Delete the temp folder recursively",
  "confirm": true
}
```

---

## Security

| Layer | Behavior |
|-------|----------|
| **Blocked patterns** | `rm -rf`, `format c:`, `DROP TABLE` → always rejected |
| **Confirmation patterns** | `Remove-Item -Recurse`, `del /f`, `shutdown`, etc. → need `confirm=true` |
| **Permissions** | Chat caller granted `read`, `write`, `execute` |
| **Timeout** | Commands killed after `TERMINAL_COMMAND_TIMEOUT` |

---

## Testing

```bash
python -m pytest tests/tools/test_terminal_tool.py tests/test_chat_tools_api.py -v
```

Tests mock OpenRouter and the terminal runner — no real shell commands in CI.

---

## Files

| File | Role |
|------|------|
| `app/tools/implementations/terminal.py` | Terminal tool |
| `app/tools/bootstrap.py` | Registers tools at startup |
| `app/tools/llm_format.py` | Tool → OpenAI function schema |
| `app/services/tool_loop.py` | LLM ↔ tool execution loop |
| `app/services/chat.py` | Wires tool loop into chat |
| `app/brain/providers/openrouter.py` | Tool calling support |

---

## Next Sprint

**Sprint 6 — Desktop automation** (mouse, keyboard, window focus). Say **"start sprint 6"** when ready.
