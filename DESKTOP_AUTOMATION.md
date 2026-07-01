# Desktop Automation — Jarvis OS Sprint 6

> Jarvis can focus windows, click, type, and capture screenshots on your desktop.

---

## Overview

Sprint 6 adds a **DesktopAutomation** port with a **Windows adapter** and four tools registered in the tool platform. They are available automatically in the chat tool loop (same as `terminal.run`).

```
Chat → ToolLoop → desktop.focus_window / type_text / click / screenshot_region
                         │
                         ▼
              WindowsDesktopAutomation
              (pygetwindow + pyautogui)
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TOOLS_ENABLED` | `true` | Master switch for all tools |
| `DESKTOP_AUTOMATION_ENABLED` | `true` | Register desktop tools |

### Dependencies (Windows)

```bash
pip install pyautogui pygetwindow
```

Included in `requirements.txt`. **Primary platform: Windows.** Linux/macOS receive a clear unsupported error.

---

## Tools

| Tool ID | LLM function name | Description |
|---------|-------------------|-------------|
| `desktop.focus_window` | `desktop_focus_window` | Focus window by title substring |
| `desktop.type_text` | `desktop_type_text` | Type into focused window |
| `desktop.click` | `desktop_click` | Click at screen coordinates |
| `desktop.screenshot_region` | `desktop_screenshot_region` | Capture screen region (base64 PNG) |

### Example chat prompt

```json
{ "message": "Open Notepad and type hello" }
```

Jarvis may call `desktop_focus_window` then `desktop_type_text`, then reply.

### Dangerous desktop actions

String parameters on `type_text` are scanned by the same security policy as terminal commands. Destructive patterns require `confirm: true` on the chat request.

---

## Architecture

```
app/tools/desktop/
├── interfaces/desktop_automation.py   # Port
├── adapters/windows.py                # Windows implementation
├── adapters/unsupported.py            # Non-Windows stub
├── factory.py                         # build_desktop_automation()
└── exceptions.py

app/tools/implementations/desktop_tools.py   # Four tool classes
app/tools/bootstrap.py                       # Registration at startup
```

---

## Platform behavior

| Platform | Behavior |
|----------|----------|
| **Windows** | Full support via pyautogui + pygetwindow |
| **Linux / macOS** | Tools register but return “not supported” errors |

---

## Testing

```bash
python -m pytest tests/tools/desktop/ tests/test_chat_desktop_api.py -v
```

Tests use `MockDesktopAutomation` — no real mouse/keyboard in CI.

---

## Safety

- `pyautogui.FAILSAFE = True` — move mouse to top-left corner to abort
- Screenshot tool is **read-only** (`read` permission)
- Click and type require `execute` + `write` permissions
- Confirmation policy applies to dangerous **text** in parameters

---

## Next sprint

**Sprint 7 — Long-term memory** across sessions. Say **"start sprint 7"** when ready.
