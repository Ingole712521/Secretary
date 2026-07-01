# Jarvis OS — Engineering Rules

> **Authority:** These rules are mandatory for all human and AI contributors.  
> **Violations block merge.** No exceptions without architect approval.

---

## 1. Non-Negotiables

| Rule | Requirement |
|------|-------------|
| Python | **3.12+** only |
| API framework | **FastAPI** |
| Type hints | **Required** on every function, method, and public attribute |
| Formatting | **Black** (no manual style debates) |
| Linting | **Ruff** (must pass with zero errors) |
| Type checking | **Mypy** (strict mode on `src/`) |
| Testing | **Unit tests required** for all new logic |
| Secrets | **`.env` only** — never in source code |
| Documentation | **Every feature must have documentation** before merge |
| Code deletion | **Never delete code without explanation** in PR/commit |

---

## 2. Language & Runtime

- Python 3.12+ with modern syntax (`match`, `type` aliases, `X | None`).
- UTF-8 encoding for all source files.
- Prefer `from __future__ import annotations` in modules with forward references.
- Use `pathlib.Path` over string paths.
- Use `collections.abc` (`Sequence`, `Mapping`, `Callable`) in interface signatures.

---

## 3. Framework & Data Models

| Rule | Standard |
|------|----------|
| API | FastAPI for all HTTP and WebSocket endpoints |
| Validation | Pydantic v2 for schemas, settings, and DTOs |
| Data classes | Use Pydantic `BaseModel` for validated data; `dataclasses` only for simple internal structs with no validation |
| HTTP client | `httpx` async client — never `requests` in async code |
| Settings | `pydantic-settings` `BaseSettings` with `SecretStr` for secrets |
| Async | Use `async`/`await` for all I/O-bound operations |
| Sync libraries | Wrap in `asyncio.to_thread()` or executor if unavoidable |

---

## 4. Architecture

### Clean Architecture — Strict Layer Rules

| Layer | May Import | Must NOT Import |
|-------|------------|-----------------|
| `domain` | stdlib | Everything else |
| `application` | `domain`, `core` | `infrastructure`, `api` |
| `infrastructure` | `application`, `domain`, `core` | `api` |
| `api` | `application`, `core` | `infrastructure` |

### Dependency Injection

- Wire all bindings in `core/dependencies.py`.
- Use cases receive dependencies via **constructor injection**.
- FastAPI `Depends()` used **only** in the API layer.
- **No global mutable singletons** for services.
- **Use interfaces** (`Protocol` or ABC) for every external dependency.

### Composition Over Inheritance

- Prefer injecting behavior via ports over subclassing adapters.
- Maximum inheritance depth: 1 (base exception or base adapter).
- Never create deep class hierarchies.

### SOLID

- **One use case per class.**
- **One tool per executor module.**
- **Small interfaces** — split large protocols into focused ones.
- **Open for extension** — register tools, don't modify core.

---

## 5. Module Design

| Rule | Limit |
|------|-------|
| File size | **Maximum 500 lines** — split if exceeded |
| Function size | Maximum 40 lines |
| Class responsibility | One reason to change |
| Module responsibility | One bounded capability |
| Naming | `snake_case` functions/modules, `PascalCase` classes, `SCREAMING_SNAKE` constants |
| Visibility | Prefix internal symbols with `_` |
| Duplication | **Never duplicate code** — extract shared logic into reusable functions or modules |

---

## 6. Type Hints

Required on **all** function signatures and public class attributes.

```python
# CORRECT
async def execute_tool(
    tool_name: str,
    params: dict[str, Any],
    *,
    timeout: float = 30.0,
) -> ToolResult:
    ...

# WRONG — missing types
async def execute_tool(tool_name, params, timeout=30.0):
    ...
```

- Prefer `X | None` over `Optional[X]`.
- Use `TypeAlias` for complex types.
- Mypy config: `disallow_untyped_defs = true`, `warn_return_any = true`.
- No `# type: ignore` without a comment explaining why.

---

## 7. Docstrings — Google Style

Required on all **public** modules, classes, and functions.

```python
async def execute_tool(
    tool_name: str,
    params: dict[str, Any],
    *,
    timeout: float = 30.0,
) -> ToolResult:
    """Execute a registered tool with validated parameters.

    Args:
        tool_name: Registered name of the tool.
        params: Input parameters matching the tool JSON Schema.
        timeout: Maximum execution time in seconds.

    Returns:
        ToolResult with output data and execution metadata.

    Raises:
        ToolNotFoundError: If the tool is not registered.
        ToolExecutionError: If execution fails or times out.
    """
```

- Module docstrings: one line describing purpose.
- Private functions (`_prefix`): docstrings optional but encouraged for complex logic.
- No redundant docstrings that restate the function name.

---

## 8. Async Patterns

```python
# CORRECT
async def fetch(url: str, client: httpx.AsyncClient) -> dict[str, Any]:
    response = await client.get(url, timeout=30.0)
    response.raise_for_status()
    return response.json()

# WRONG — blocking call in async context
async def fetch(url: str) -> dict[str, Any]:
    return requests.get(url).json()
```

- `asyncio.gather()` for concurrent independent I/O.
- `async with` for all resource lifecycles.
- Always set explicit timeouts on external calls.
- Never use `time.sleep()` in async code — use `asyncio.sleep()`.

---

## 9. Configuration & Secrets

| Rule | Detail |
|------|--------|
| **Never hardcode values** | URLs, ports, API keys, tokens, paths — all from config |
| Secrets | Environment variables only; `SecretStr` in settings |
| Local dev | `.env` file (gitignored); `.env.example` documents required vars |
| Defaults | Safe, non-secret defaults only |
| Production | K8s Secrets, AWS SSM, or equivalent |

```python
# CORRECT
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    api_key: SecretStr
    api_port: int = 8000

# WRONG
API_KEY = "sk-abc123"
BASE_URL = "https://api.example.com"  # use config
```

---

## 10. Error Handling

- Define exceptions in `core/exceptions.py` or `domain/`.
- Hierarchy: `JarvisError` → `DomainError` / `ApplicationError` / `InfrastructureError`.
- Never catch bare `Exception` unless re-raising or in top-level handler.
- Never swallow errors silently.
- Map domain exceptions to HTTP status in API layer only.
- Include `correlation_id` in all error logs and responses.

---

## 11. Logging

- Use stdlib `logging` — **never `print()`** in production code.
- **Structured logging** (JSON) in production; human-readable in development.
- Every request gets a **correlation ID** propagated through all log records.
- Levels: DEBUG (dev only), INFO (operations), WARNING (recoverable), ERROR (failures).
- **Never log:** secrets, tokens, passwords, full PII, complete sensitive tool params.

```python
logger.info(
    "Tool executed",
    extra={
        "tool_name": tool_name,
        "duration_ms": duration,
        "success": True,
        "correlation_id": correlation_id,
    },
)
```

---

## 12. Testing

| Rule | Requirement |
|------|-------------|
| Framework | pytest + pytest-asyncio |
| Required | Unit test for every new use case, domain service, and adapter |
| Naming | `test_<what>_<condition>_<expected>` |
| Mocking | Mock ports in use case tests; never hit real APIs in unit tests |
| Coverage | ≥ 80% for `domain` and `application` layers |
| Async | `@pytest.mark.asyncio` on all async tests |
| Fixtures | Shared fixtures in `tests/conftest.py` |

```python
@pytest.mark.asyncio
async def test_execute_tool_when_not_found_raises_error() -> None:
    """ToolNotFoundError raised for unregistered tool name."""
    executor = ToolExecutor(registry=empty_registry)
    with pytest.raises(ToolNotFoundError):
        await executor.execute("nonexistent", {})
```

---

## 13. API Design

- Version all routes under `/v1/`.
- Request/response schemas in `api/v1/schemas/` — separate from domain entities.
- Thin route handlers: validate → call use case → map response.
- Consistent error envelope: `{ "error": { "code", "message", "correlation_id" } }`.
- Document with FastAPI `summary`, `description`, `response_model`.

---

## 14. Security

- Validate all input at API boundary (Pydantic).
- Sanitize tool parameters before execution.
- Least privilege for all integration credentials.
- No `eval()`, `exec()`, or `__import__()` on user input.
- Shell commands: allowlist or explicit approval gate.
- CORS: explicit origins only in production.
- Auth on all endpoints except `/health` and `/ready`.

---

## 15. Documentation

Every feature PR must include documentation updates:

| Change | Update |
|--------|--------|
| New subsystem or flow | `ARCHITECTURE.md` |
| New requirement | `PROJECT.md` |
| New dependency | `TECH_STACK.md` |
| Phase completion | `ROADMAP.md` |
| Public API | Google docstring + OpenAPI metadata |
| Onboarding impact | `SYSTEM_OVERVIEW.md` |

- No duplication across docs — link to the canonical source.
- Mermaid diagrams for complex flows in `ARCHITECTURE.md`.

---

## 16. Code Deletion

- **Never delete code without explanation** in the commit message or PR description.
- State what was removed, why, and what replaces it (if applicable).
- Confirm tests pass after deletion.
- Git preserves history — prefer deletion over commenting out.

---

## 17. Git & Commits

- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- One logical change per commit.
- No `.env`, credentials, `__pycache__`, or build artifacts in commits.
- PRs require passing CI before merge.

---

## 18. Prohibited Patterns

| Pattern | Why |
|---------|-----|
| God classes | Violates SRP |
| Circular imports | Fix architecture |
| `import *` | Explicit imports only |
| Mutable default arguments | Use `None` + factory |
| Global mutable state | Use DI |
| Direct DB/SDK calls from API routes | Go through use cases |
| `print()` for logging | Use `logging` module |
| Commented-out code | Delete with explanation |
| Copy-pasted logic | Extract to shared module |
| Hardcoded config values | Use `Settings` |
| Deep inheritance trees | Use composition |
| TODO without issue reference | Create ticket or fix now |
| Files &gt; 500 lines | Split into modules |

---

## 19. AI Agent Instructions (Cursor)

Before writing any code:

1. Read `SYSTEM_OVERVIEW.md`, `ARCHITECTURE.md`, and `ROADMAP.md`.
2. Implement **only** the current phase scope.
3. Create port interfaces before infrastructure adapters.
4. Write tests alongside implementation.
5. Run `ruff check .`, `black --check .`, `mypy src`, `pytest` before finishing.
6. Update documentation for any public API or architectural change.
7. Do not add dependencies without updating `TECH_STACK.md`.
8. Do not introduce experimental or pre-release libraries.
9. Match existing code style in the file being edited.
10. Never delete code without explaining why.

---

## 20. Pre-Merge Checklist

- [ ] Python 3.12+ features used correctly
- [ ] Type hints on all public APIs
- [ ] Google-style docstrings on public modules/classes/functions
- [ ] Ruff — zero errors
- [ ] Black — formatted
- [ ] Mypy — zero errors
- [ ] pytest — all passing
- [ ] No secrets or hardcoded config in diff
- [ ] No file exceeds 500 lines
- [ ] No duplicated logic
- [ ] Dependency rules respected (Clean Architecture)
- [ ] Structured logging with correlation ID
- [ ] Documentation updated
- [ ] Phase scope not exceeded
- [ ] Code deletion explained (if applicable)
