# Tool Platform — Jarvis OS

> **Sprint 3** — Generic tool execution framework. No concrete tools (terminal, browser, GitHub, etc.) are implemented yet.

---

## 1. Overview

The Tool Platform lets Jarvis OS **register**, **validate**, **authorize**, and **execute** tools safely. It is the foundation for all future automation: terminal, browser, GitHub, desktop, cloud, and custom plugins.

```
AI / Brain / Agents
        │
        ▼
  ToolExecutor
        │
   ┌────┴────┬────────────┬──────────┐
   ▼         ▼            ▼          ▼
Registry  Validator   Security   Sandbox
```

---

## 2. Package Structure

```
app/tools/
├── interfaces/       # Tool protocol + BaseTool
├── schemas/          # Requests, responses, definitions, enums
├── registry/         # ToolRegistry
├── executor/         # ToolExecutor
├── permissions/      # PermissionGrant, PermissionChecker
├── results/          # ToolResult (success, failure, warning, retry, cancelled)
├── validators/       # Parameter, permission, security, composite
├── security/         # Policies, whitelist/blacklist, Sandbox port
├── exceptions/       # Tool platform errors
└── factory.py        # build_tool_platform()
```

---

## 3. Tool Interface

Every tool implements the `Tool` protocol (or extends `BaseTool`):

| Member | Type | Description |
|--------|------|-------------|
| `id` | `str` | Unique identifier (e.g. `terminal.run`) |
| `name` | `str` | Human-readable name |
| `description` | `str` | What the tool does |
| `category` | `ToolCategory` | Grouping for search |
| `parameters` | `list[ToolParameter]` | Input schema |
| `permissions` | `list[ToolPermissionLevel]` | Required permissions |
| `execute()` | async | Run the tool |
| `validate()` | async | Validate inputs |
| `dry_run()` | async | Simulate without side effects |
| `health()` | async | Report operational status |

### Example (future tool)

```python
from app.tools import BaseTool
from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter

class MyTool(BaseTool):
    @property
    def id(self) -> str:
        return "my.tool"

    # ... other properties ...

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        return ToolResult.success(output={"done": True})
```

---

## 4. How Tools Register

```python
from app.tools import build_tool_platform

platform = build_tool_platform()
platform.registry.register(MyTool())
```

### Registry API

| Method | Description |
|--------|-------------|
| `register(tool)` | Add a tool |
| `unregister(tool_id)` | Remove a tool |
| `find(tool_id)` | Get tool instance |
| `get_definition(tool_id)` | Get metadata only |
| `list_tools()` | All definitions |
| `search(query)` | Search by name/description/tags |
| `group_by_category()` | Group by `ToolCategory` |

Registration happens at application startup (via `build_tool_platform()` in `ServiceContainer`) or dynamically when plugins load.

---

## 5. How Execution Works

```python
from app.tools.schemas.enums import ToolPermissionLevel
from app.tools.schemas.requests import ToolExecutionRequest

request = ToolExecutionRequest(
    tool_id="my.tool",
    parameters={"key": "value"},
    caller_permissions=[ToolPermissionLevel.READ, ToolPermissionLevel.EXECUTE],
    correlation_id="uuid",
    dry_run=False,
)

response = await platform.executor.execute(request)
```

### Execution Pipeline

```
1. Find tool in Registry
2. Validate parameters (schema)
3. Check caller permissions
4. Enforce security policy (whitelist, blacklist, dangerous patterns)
5. Require confirmation if policy demands it
6. Optional: prepare Sandbox
7. tool.validate() → tool.execute() or tool.dry_run()
8. Capture result, logs, duration_ms
9. Append to audit log
10. Return ToolExecutionResponse
```

### Response Structure

```python
ToolExecutionResponse
├── tool_id
├── result: ToolResult
├── duration_ms
├── logs: list[str]
├── correlation_id
├── validated: bool
└── permission_granted: bool
```

---

## 6. Tool Results

| Status | Factory | Use Case |
|--------|---------|----------|
| `SUCCESS` | `ToolResult.success()` | Completed normally |
| `FAILURE` | `ToolResult.failure()` | Error occurred |
| `WARNING` | `ToolResult.warning()` | Completed with warnings |
| `RETRY` | `ToolResult.retry()` | Transient failure, retry later |
| `CANCELLED` | `ToolResult.cancelled()` | User or system cancelled |

---

## 7. Permissions

### Standard Levels

| Level | Description |
|-------|-------------|
| `READ` | Read-only operations |
| `WRITE` | Modify data or state |
| `EXECUTE` | Run commands or tools |
| `ADMIN` | Elevated operations |
| `SYSTEM` | OS-level access |
| `CUSTOM` | Tool-specific custom strings |

### Permission Model

- Each tool declares `permissions: list[ToolPermissionLevel]`
- Each request carries `caller_permissions` from the agent/user context
- `PermissionChecker` validates grants; `ADMIN` and `SYSTEM` supersede lower levels

---

## 8. Security

### ToolSecurityPolicy

| Field | Description |
|-------|-------------|
| `whitelist` | Allowed tool IDs (empty = all allowed) |
| `blacklist` | Blocked tool IDs |
| `confirmation_policy` | `never`, `on_dangerous`, `on_write`, `always` |
| `dangerous_patterns` | Regex patterns blocked in string params |
| `require_sandbox` | Enable sandbox port |

### Dangerous Command Detection

String parameters are scanned for patterns like `rm -rf`, `sudo`, `DROP TABLE`. Matches raise `ToolSecurityError`.

### Confirmation

High-risk tools (ADMIN/SYSTEM permissions) require `metadata.confirmed=True` on the request when `confirmation_policy=on_dangerous`.

### Sandbox Interface

```python
class Sandbox(Protocol):
    async def prepare(self, tool_id: str) -> None: ...
    async def execute_isolated(self, tool_id: str, params: dict) -> object: ...
    async def cleanup(self, tool_id: str) -> None: ...
```

Sprint 3 ships `NoOpSandbox`. Real isolation comes in a future sprint.

---

## 9. Validation Layers

| Validator | Responsibility |
|-----------|----------------|
| `ParameterValidator` | Schema types, required fields, enums, defaults |
| `PermissionValidator` | Caller vs tool permissions |
| `SecurityPolicyValidator` | Whitelist, blacklist, dangerous patterns, confirmation |
| `ToolValidator` | Orchestrates all three |

---

## 10. Exceptions

| Exception | HTTP | When |
|-----------|------|------|
| `ToolNotFoundError` | 500 | Tool ID not registered |
| `ToolValidationError` | 422 | Invalid parameters |
| `ToolPermissionDeniedError` | 403 | Insufficient permissions |
| `ToolSecurityError` | 500 | Policy violation |
| `ToolConfirmationRequiredError` | 500 | Needs human approval |
| `ToolExecutionError` | 500 | Runtime failure |

---

## 11. Dependency Injection

```python
# app/dependencies/container.py
ServiceContainer
├── settings
├── health_service
├── brain
└── tools: ToolPlatformContainer
        ├── registry
        ├── executor
        ├── validator
        └── security
```

Access in FastAPI (future):

```python
def get_tools(request: Request) -> ToolPlatformContainer:
    return request.app.state.container.tools
```

---

## 12. How Future Tools Plug In

### Step 1 — Implement `BaseTool`

Create `app/tools/implementations/terminal.py` (example, not in Sprint 3).

### Step 2 — Register at startup

```python
def build_tool_platform() -> ToolPlatformContainer:
    container = ...
    container.registry.register(TerminalTool())
    container.registry.register(BrowserTool())
    return container
```

### Step 3 — Brain / Agent invokes executor

```python
request = ToolExecutionRequest(
    tool_id="terminal.run",
    parameters={"command": "git status"},
    caller_permissions=agent.permissions,
)
response = await tools.executor.execute(request)
```

### Step 4 — Audit and memory (future)

- Audit log feeds observability
- Results stored in episodic memory via Brain

---

## 13. Integration with Brain

```
Orchestrator
    → Planner (generates plan with tool steps)
    → Agent Orchestrator (future)
        → ToolExecutor.execute() per step
```

The Brain does not call tools directly in Sprint 3. Integration wiring is a future sprint task.

---

## 14. Sprint 3 Boundaries

### In Scope

- Full framework architecture
- Registry, executor, validators, security, permissions, results
- DI via `ServiceContainer.tools`
- Test stub tool in `tests/tools/` only
- Documentation

### Out of Scope

- Terminal, browser, GitHub, desktop tools
- REST API endpoints for tools
- Persistent audit log storage
- Real sandbox isolation
- Brain orchestrator → tool wiring

---

## 15. Quality

- SOLID: single-responsibility modules, port/adapter pattern
- DI: `build_tool_platform()` wires all components
- All public classes documented with Google-style docstrings
- No file exceeds 400 lines
- 50+ tests across registry, executor, DI
