# Sprint 1 — Architectural Review

> **Reviewer role:** Principal Software Engineer  
> **Scope:** Sprint 1 backend foundation only  
> **Date:** 2026-07-01  
> **Verdict:** Approved for Sprint 2 with documented technical debt

---

## Overall Architecture Score: **7.5 / 10**

Sprint 1 delivers a solid, runnable FastAPI foundation with good typing, testing discipline, and clear separation of concerns for a greenfield project. It is **not yet** fully aligned with the Clean Architecture described in `ARCHITECTURE.md`, but the structure is intentionally pragmatic and refactor-friendly. After the refactors performed in this review, the codebase is **ready for Sprint 2 (AI Router)** with known, documented gaps.

---

## 1. Folder Structure

### Evaluation

```
app/
├── api/              # HTTP routes
├── application/      # Placeholder for future use cases
├── config/           # Settings
├── core/             # App factory, logging, lifecycle, middleware setup
├── dependencies/     # FastAPI Depends + DI container
├── exceptions/       # Domain error hierarchy
├── interfaces/       # Port protocols (AI, memory, tools)
├── middleware/       # HTTP middleware + exception handlers
├── models/           # API response schemas
├── services/         # Application services
└── utils/            # Shared utilities
main.py
tests/
scripts/
logs/
data/
```

### Strengths

- Logical package boundaries with single responsibilities per folder.
- `main.py` at project root is a standard, discoverable entry point.
- `tests/` mirrors application concerns (config, API, health, exceptions, utils).

### Weaknesses

| Issue | Severity | Notes |
|-------|----------|-------|
| Divergence from `ARCHITECTURE.md` | Medium | Docs describe `domain/`, `application/use_cases/`, `infrastructure/` — not yet implemented |
| `models/` naming collision risk | Low | Pydantic API schemas share name with ORM "models" used in later phases |
| `middleware/error_handling.py` is not middleware | Low | Exception handlers are not ASGI middleware; naming is misleading |

### Refactoring Performed

- Added `app/application/` placeholder package for future use case migration.
- Added `app/interfaces/` for port protocols (extracted from `dependencies/container.py`).
- Added `app/constants.py` for shared constants.
- Extracted `app/core/lifespan.py` and `app/core/middleware_setup.py` from `app.py`.

---

## 2. Package Organization

### Strengths

- Clear import direction: `api` → `dependencies` → `services` → `config/utils`.
- No circular imports detected.
- `__init__.py` files export public APIs cleanly.

### Weaknesses

| Issue | Why It Matters |
|-------|----------------|
| `services/` acts as both application and domain logic | Health logic is trivial today; will blur as features grow |
| Protocols were inside `dependencies/container.py` | Violates interface segregation; container should wire, not define contracts |

### Refactoring Performed

- Moved `AIRouterServiceProtocol`, `MemoryServiceProtocol`, `ToolServiceProtocol` to `app/interfaces/protocols.py`.
- `ServiceContainer` now only holds instances and `build_container()` wiring.

---

## 3. Naming Conventions

### Strengths

- Consistent `snake_case` modules, `PascalCase` classes.
- Logger names namespaced under `jarvis.*`.
- Test names follow `test_<what>_<condition>_<expected>` pattern.

### Weaknesses

| Issue | Recommendation |
|-------|----------------|
| `models/` = API schemas | Rename to `schemas/` in Sprint 2+ when API surface grows |
| `CORRELATION_ID_STATE_KEY` vs header name | Now centralized in `constants.py` |

### Refactoring Performed

- Centralized logger name constants in `app/constants.py`.
- Unified correlation ID state key usage across middleware and error handlers.

---

## 4. Clean Architecture Compliance

### Score: **6 / 10** (appropriate for Sprint 1)

| Layer (Target) | Sprint 1 Reality | Status |
|----------------|------------------|--------|
| Domain | `exceptions/` only | Partial |
| Application | `services/` | Transitional |
| Infrastructure | Not present | Expected |
| Presentation | `api/` | Good |

### Issues

1. **HealthService returns API models directly** — couples service layer to presentation schemas.
2. **No repository or port abstractions** beyond future protocol stubs.
3. **`ARCHITECTURE.md` documents `src/jarvis/` layout** — implementation uses `app/` at root.

### Why This Is Acceptable Now

Sprint 1 scope is infrastructure-only. Premature `domain/` and `infrastructure/` packages would be empty ceremony. The `application/` placeholder and `interfaces/` package establish the migration path.

### Recommended Sprint 2 Migration

```
app/services/health.py     → app/application/use_cases/health.py
app/models/health.py       → app/api/schemas/health.py
app/interfaces/protocols.py → app/application/interfaces/ (move)
```

---

## 5. SOLID Principles

| Principle | Score | Assessment |
|-----------|-------|------------|
| **S** — Single Responsibility | 8/10 | Modules are focused; `create_app` was doing too much (fixed) |
| **O** — Open/Closed | 7/10 | Protocol stubs enable extension; container requires manual wiring per service |
| **L** — Liskov Substitution | N/A | No inheritance hierarchies yet |
| **I** — Interface Segregation | 8/10 | Small protocols; improved by moving to `interfaces/` |
| **D** — Dependency Inversion | 7/10 | Routes depend on services via DI; services depend on concrete Settings |

### Issue Fixed: Exception Status Map

**Problem:** `_STATUS_MAP.get(type(exc))` failed for exception subclasses — subclass instances would incorrectly return HTTP 500.

**Fix:** Added `app/core/exception_mapping.py` with `isinstance`-based resolution ordered from most specific to general.

---

## 6. Dependency Injection

### Strengths

- `ServiceContainer` dataclass with explicit `build_container()`.
- FastAPI `Depends()` for route-level injection.
- `HealthServiceDep` type alias improves readability.

### Issues Found & Fixed

| Issue | Problem | Fix |
|-------|---------|-----|
| Duplicate container build | `create_app()` and `lifespan` both called `build_container()` | Removed rebuild from lifespan; container built once in `create_app()` |
| `SettingsDep` used `get_settings()` cache | Test overrides via `create_app(test_settings)` would diverge from `get_settings()` | Added `get_app_settings(request)` reading `app.state.settings` |
| Global settings cache | `lru_cache` on `get_settings()` prevents runtime reload | Added `clear_settings_cache()` for tests and future reload |

### Backwards Compatibility

- All existing endpoints (`/`, `/health`, `/version`) unchanged.
- `get_settings()` still works for `main.py` and non-request contexts.
- `SettingsDep` now correctly reflects per-app settings.

---

## 7. FastAPI Best Practices

### Strengths

- `create_app()` factory pattern enables test isolation.
- Lifespan context manager for startup/shutdown.
- OpenAPI docs disabled in production.
- Response models declared on all routes.
- Thin route handlers delegating to services.

### Issues Fixed

| Issue | Fix |
|-------|-----|
| `async def` on sync service calls | Changed health routes to sync `def` — avoids unnecessary async overhead |
| Middleware order undocumented | `configure_middleware()` documents Starlette execution order |
| `api_prefix` setting unused | Documented as deferred; routes remain at root for backwards compatibility |

### Remaining Gaps

- No `/ready` endpoint (mentioned in architecture docs, not in Sprint 1 spec).
- No API versioning prefix (`/v1`) applied to routes yet.
- No `HTTPException` usage in routes (acceptable for health-only API).

---

## 8. Configuration Management

### Strengths

- `pydantic-settings` with typed fields and `SecretStr`.
- Environment enum: `development`, `testing`, `staging`, `production`.
- Production guards: no debug, no default secret key.
- `_env_file=None` pattern for test isolation.
- `populate_by_name=True` allows field names and aliases.

### Issues Fixed

| Issue | Fix |
|-------|-----|
| Staging had no secret validation | Added staging secret key check |
| Invalid `LOG_LEVEL` accepted silently | Added normalization and fallback to INFO in `setup_logging()` |
| No cache invalidation helper | Added `clear_settings_cache()` |

### Remaining Gaps

- `get_settings()` singleton can diverge from `app.state.settings` if both are used — document that request-scoped code must use `SettingsDep` or `app.state.settings`.
- No config validation for empty `cors_origins` in production.

---

## 9. Logging Architecture

### Strengths

- Structured JSON logging in production.
- Console + rotating file handlers.
- File logging disabled in testing.
- Request logging middleware with duration, method, path, status.
- Correlation ID propagated to log `extra` fields.

### Issues Fixed

- Logger names centralized in `constants.py`.
- Invalid log levels handled gracefully.

### Remaining Gaps

| Gap | Risk | Sprint |
|-----|------|--------|
| No log context variable (`contextvars`) for correlation ID in non-request code | Medium | 2 |
| `setup_logging()` clears all root handlers — may conflict with pytest caplog | Low | 2 |
| JSON formatter does not include `service` or `environment` fields | Low | 2 |

---

## 10. Exception Handling

### Strengths

- Clear hierarchy: `JarvisError` → typed subclasses.
- Standardized error envelope: `{ "error": { "code", "message", "correlation_id" } }`.
- Separate handlers for validation, HTTP, domain, and unhandled exceptions.
- Secrets not exposed in 500 responses.

### Issues Fixed

- Subclass status code resolution (see §5).
- Unused imports removed from error handler module.
- Correlation ID key unified via `constants.py`.

### Remaining Gaps

- Validation errors do not include field-level detail in response (intentional for security; may add in dev mode).
- `ToolException` and `ConfigurationException` defined but unused (expected — reserved for Phase 4).

---

## 11. Middleware Design

### Execution Order (Request → Response)

```
CORS → Request ID → Request Logging → Route Handler
```

### Strengths

- Correlation ID propagated to response headers.
- Request duration logged after response.
- CORS origins from configuration.

### Issues Fixed

| Issue | Fix |
|-------|-----|
| Middleware registration scattered in `create_app()` | Extracted to `configure_middleware()` |
| CORS `allow_methods=["*"]` in all environments | Production restricts methods and headers |
| `RequestIdMiddleware` used `app: object` with `# type: ignore` | Typed as `ASGIApp` |

### Remaining Gaps

- No security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`) — add in Sprint 16 or earlier hardening pass.
- `BaseHTTPMiddleware` has known performance limitations at scale — consider pure ASGI middleware later.

---

## 12. Test Structure

### Score: **8 / 10**

| File | Coverage |
|------|----------|
| `test_config.py` | Settings validation, environments |
| `test_health.py` | All health endpoints |
| `test_api.py` | Correlation ID, CORS, OpenAPI |
| `test_exceptions.py` | Status mapping, error envelope |
| `test_utils.py` | All utility modules |
| `test_dependencies.py` | App state settings, container wiring |

### Strengths

- 27 tests, all passing.
- `conftest.py` with settings cache clearing and test settings fixture.
- Tests isolated from `.env` file via `_env_file=None`.

### Gaps Added in Review

- Exception handler integration test.
- Utility module tests.
- Dependency wiring tests.

### Remaining Gaps

- No middleware unit tests in isolation.
- No production CORS restriction test.
- No coverage threshold enforced in CI yet.

---

## 13. Security Concerns

| Concern | Severity | Status |
|---------|----------|--------|
| Default API secret in dev | Medium | Blocked in production/staging |
| CORS wildcard methods/headers | Medium | Fixed for production |
| No authentication on endpoints | Low | Expected for Sprint 1 health API |
| `DEBUG=true` in `.env.example` | Low | Documented; blocked in production |
| Secrets in logs | Low | Not logging sensitive fields |
| No rate limiting | Low | Deferred to Sprint 2+ |
| No TLS termination config | Low | Deployment concern (Sprint 16) |
| `.env` in gitignore | OK | Verified |

### Recommendations for Sprint 2

- Add API key middleware using `api_secret_key` before exposing AI endpoints.
- Never log LLM prompts containing user PII.

---

## 14. Scalability

| Area | Sprint 1 State | Future Need |
|------|----------------|-------------|
| Stateless API | Yes — no in-memory session state | Good |
| Container singleton | Built per app instance | Good for horizontal scaling |
| File-based logging | Rotating files on each instance | Move to centralized logging (Sprint 16) |
| `lru_cache` settings | Single-process cache | Use `app.state` or env injection in workers |
| Sync health endpoints | Fine at low scale | Adequate for probes |
| `BaseHTTPMiddleware` | Fine for MVP | Replace at high throughput |

---

## 15. Maintainability

### Strengths

- All modules under 200 lines (well under 500-line limit).
- Google-style docstrings on public functions.
- Full type hints; Mypy strict passes.
- Ruff + Black compatible.
- `pyproject.toml` centralizes tooling.

### Weaknesses

- Documentation (`ARCHITECTURE.md`) out of sync with `app/` layout.
- `api_prefix` configured but unused — confusing for new developers.

---

## Strengths (Summary)

1. **Production-minded foundation** — structured logging, correlation IDs, error envelopes, environment validation.
2. **Strong typing and tooling** — Mypy strict, Ruff, Black, 27 tests.
3. **Clear extension points** — `interfaces/`, `ServiceContainer`, protocol stubs for AI/memory/tools.
4. **Testable app factory** — `create_app(settings)` enables full isolation.
5. **Security awareness** — production secret enforcement, CORS restrictions, no secrets in error responses.
6. **Thin API layer** — routes delegate to services via DI.

---

## Weaknesses (Summary)

1. **Clean Architecture gap** — `ARCHITECTURE.md` describes layers not yet implemented.
2. **Naming** — `models/` should become `schemas/`; `error_handling` is not middleware.
3. **API versioning** — `API_PREFIX=/v1` not applied to routes.
4. **No auth middleware** — required before Sprint 2 AI endpoints.
5. **Settings dual-access** — both `get_settings()` cache and `app.state.settings` coexist.
6. **No CI pipeline** — quality checks documented but not automated in GitHub Actions.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Architecture drift as features are added | High | High | Enforce layer rules in Sprint 2; migrate to `application/use_cases/` |
| `get_settings()` vs `app.state.settings` divergence | Medium | Medium | Use `SettingsDep` in all routes; document rule |
| Services grow into god objects | Medium | High | One use case per class starting Sprint 2 |
| Middleware performance at scale | Low | Medium | Monitor; refactor to ASGI middleware if needed |
| TestClient deprecation warning (httpx) | Low | Low | Migrate to `httpx` AsyncClient in tests when stable |

---

## Technical Debt

| Item | Priority | Target Sprint |
|------|----------|---------------|
| Rename `models/` → `schemas/` | Medium | 2 |
| Align `ARCHITECTURE.md` folder structure with `app/` | High | 2 |
| Apply `/v1` API prefix (with backwards-compatible aliases) | Medium | 2 |
| Add `/ready` endpoint | Low | 2 |
| Move health logic to use case pattern | Medium | 2 |
| Add API key authentication middleware | High | 2 |
| Add GitHub Actions CI (ruff, black, mypy, pytest) | High | 2 |
| Add `contextvars` for correlation ID in non-request code | Medium | 2 |
| Security headers middleware | Medium | 16 |
| Rename `middleware/error_handling.py` → `core/exception_handlers.py` | Low | 3 |

---

## Suggested Improvements (Sprint 2 Prep)

1. **Create `app/application/use_cases/`** — move business logic out of `services/`.
2. **Create `app/infrastructure/llm/`** — first adapter implementing `LLMProvider` protocol.
3. **Add auth middleware** — validate `Authorization` header against `api_secret_key`.
4. **Mount routes at `/v1`** — keep `/health` alias at root for probe backwards compatibility.
5. **Add CI pipeline** — GitHub Actions running ruff, black, mypy, pytest on every PR.
6. **Expand `ServiceContainer`** — register `LLMProvider` adapter via `build_container()`.
7. **Update `ARCHITECTURE.md`** — reflect actual `app/` package structure.

---

## Readiness for Sprint 2

| Criterion | Ready? | Notes |
|-----------|--------|-------|
| Runnable FastAPI app | Yes | `python main.py` or `uvicorn main:app` |
| DI container extensible | Yes | Add services in `build_container()` |
| Port interfaces defined | Yes | `interfaces/protocols.py` |
| Exception hierarchy | Yes | Ready for `RouterError`, `ProviderError` |
| Logging + correlation ID | Yes | Ready for LLM request tracing |
| Config for LLM keys | Partial | `.env.example` has placeholders; add to `Settings` |
| Tests as quality gate | Yes | 27 passing; add CI |
| Auth before AI endpoints | No | **Must add in Sprint 2 before `/v1/chat`** |

### Verdict: **READY for Sprint 2** with the requirement that API authentication is the first task before exposing any AI endpoint.

---

## Refactoring Performed

| Change | Files | Backwards Compatible |
|--------|-------|---------------------|
| Extract protocols to `app/interfaces/` | `interfaces/protocols.py`, `dependencies/container.py` | Yes |
| Extract lifespan to `app/core/lifespan.py` | `core/lifespan.py`, `core/app.py` | Yes |
| Extract middleware setup | `core/middleware_setup.py` | Yes |
| Fix exception status code resolution | `core/exception_mapping.py`, `middleware/error_handling.py` | Yes |
| Fix `SettingsDep` to use `app.state.settings` | `dependencies/__init__.py` | Yes |
| Remove duplicate container build in lifespan | `core/lifespan.py` | Yes |
| Add `clear_settings_cache()` | `config/settings.py` | Yes |
| Centralize constants | `constants.py`, middleware, logging, main | Yes |
| Production CORS restrictions | `middleware/cors.py` | Yes (dev unchanged) |
| Staging secret validation | `config/settings.py` | Yes |
| Log level validation fallback | `core/logging.py` | Yes |
| Sync health route handlers | `api/routes/health.py` | Yes |
| Add `application/` placeholder package | `application/__init__.py` | Yes |
| Expand test suite (14 → 27 tests) | `test_exceptions.py`, `test_utils.py`, `test_dependencies.py` | N/A |

### Quality Gate After Refactoring

```
pytest:  27 passed
ruff:    All checks passed
mypy:    Success (42 source files)
black:   Formatted
```

---

## Review Sign-Off

Sprint 1 establishes a **credible, production-oriented backend skeleton**. The refactors in this review address the highest-risk issues (DI correctness, exception mapping, CORS, duplicate initialization) without breaking existing endpoints. The team may proceed to **Sprint 2 — AI Router** after adding authentication middleware and updating architecture documentation to match the implemented structure.
