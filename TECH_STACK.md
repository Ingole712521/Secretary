# Jarvis OS — Technology Stack

> **Audience:** Engineers and operators selecting libraries, services, and infrastructure.  
> **Rule:** Do not add dependencies outside this document without updating it and [ROADMAP.md](ROADMAP.md).

---

## Overview

| Layer | Phase Introduced | Technology |
|-------|-----------------|------------|
| Runtime | 0 | Python 3.12+ |
| API | 1 | FastAPI, Uvicorn |
| Validation | 0 | Pydantic v2, pydantic-settings |
| Database | 3 | PostgreSQL |
| Vector store | 3 | pgvector (primary) |
| Cache / Queue | 14 | Redis |
| Voice | 6 | Provider TBD (see below) |
| Vision | 7 | Multimodal LLM + screen capture |
| Desktop | 5 | Platform-specific adapters |
| Browser | 8 | Playwright |
| Containers | 10 | Docker |
| Orchestration | 11 | Kubernetes |
| Cloud | 12–13 | AWS (boto3), Hostinger API |
| Deployment | 16 | Docker, K8s, CI/CD |
| Testing | 1 | pytest, pytest-asyncio |
| Monitoring | 16 | Prometheus-compatible metrics |
| Logging | 1 | stdlib `logging` + structured JSON |

---

## Programming Language

| Item | Choice | Rationale |
|------|--------|-----------|
| Language | **Python 3.12+** | Rich AI/automation ecosystem, strong typing, async support |
| Package manager | `pip` + `venv` (initial); `uv` optional | Simple onboarding; `uv` for faster installs later |
| Type checking | **Mypy** (strict) | Catch errors before runtime |
| Linting | **Ruff** | Fast, replaces flake8/isort |
| Formatting | **Black** | Consistent style, zero debate |

---

## Framework

| Item | Choice | Phase | Notes |
|------|--------|-------|-------|
| API framework | **FastAPI** | 1 | Async-native, OpenAPI auto-generation |
| ASGI server | **Uvicorn** `[standard]` | 1 | Production-ready with uvloop |
| HTTP client | **httpx** | 0 | Async external API calls |
| Settings | **pydantic-settings** | 1 | Typed config from environment |
| DI | FastAPI `Depends()` + `core/dependencies.py` | 1 | Constructor injection in use cases |

---

## Database

| Item | Choice | Phase | Notes |
|------|--------|-------|-------|
| Primary DB | **PostgreSQL 16+** | 3 | Plans, audit logs, sessions, metadata |
| ORM / driver | **SQLAlchemy 2.x** (async) or raw async driver | 3 | Decision at Phase 3 implementation |
| Migrations | **Alembic** | 3 | Version-controlled schema changes |
| Dev fallback | SQLite (async) | 3 | Local development only — not for production |

---

## Vector Database

| Item | Choice | Phase | Notes |
|------|--------|-------|-------|
| Primary | **pgvector** extension on PostgreSQL | 3 | Co-located with relational data |
| Alternative | Dedicated vector DB (e.g., Qdrant) | 3+ | Evaluate if pgvector performance insufficient |
| Embeddings | Provider API (OpenAI, etc.) | 3 | Configurable via `EMBEDDING_MODEL` |

---

## Voice

| Item | Choice | Phase | Notes |
|------|--------|-------|-------|
| STT | **OpenAI Whisper API** or local Whisper | 6 | Local option for privacy |
| TTS | Provider TBD (OpenAI, ElevenLabs, or edge-tts) | 6 | Selected at Phase 6 based on latency/cost |
| Transport | **WebSocket** | 6 | Real-time audio streaming |
| Protocol | PCM / Opus audio frames over WS | 6 | Defined in Phase 6 API spec |

---

## Vision

| Item | Choice | Phase | Notes |
|------|--------|-------|-------|
| Screen capture | Platform-native + **mss** or equivalent | 7 | Cross-platform capture library |
| Analysis | **Multimodal LLM** (GPT-4o, Claude, etc.) | 7 | Via existing LLM provider adapter |
| Image format | PNG / JPEG | 7 | Configurable quality for bandwidth |

---

## Automation

| Domain | Choice | Phase | Notes |
|--------|--------|-------|-------|
| Terminal | `asyncio.create_subprocess_exec` | 4 | Sandboxed shell with allowlist |
| Desktop (Windows) | **pyautogui** + Win32 APIs | 5 | Primary platform |
| Desktop (macOS/Linux) | Platform stubs → native adapters | 5+ | Implemented after Windows |
| Browser | **Playwright** | 8 | Headless and headed modes |
| File system | stdlib `pathlib`, `aiofiles` | 4+ | Async file I/O |

---

## Desktop

| Platform | Library / API | Phase |
|----------|--------------|-------|
| Windows | Win32, pyautogui, pywinauto (evaluate) | 5 |
| macOS | AppleScript, Quartz (stub) | 5+ |
| Linux | X11/Wayland adapters (stub) | 5+ |

All desktop operations exposed exclusively through the Tool Framework (Phase 4).

---

## Browser

| Item | Choice | Phase |
|------|--------|-------|
| Driver | **Playwright** (Python) | 8 |
| Session management | Browser contexts per task | 8 |
| Safety | Domain allowlist via config | 8 |

---

## Memory

| Component | Technology | Phase |
|-----------|-----------|-------|
| Relational storage | PostgreSQL | 3 |
| Vector search | pgvector | 3 |
| Cache (hot memories) | Redis | 14 |
| Embedding generation | LLM provider API | 3 |

---

## Queue

| Item | Choice | Phase | Notes |
|------|--------|-------|-------|
| Message broker | **Redis** (Streams or BullMQ pattern) | 14 | Plan step dispatch, async jobs |
| Alternative | AWS SQS | 16 | For AWS-native deployments |
| Worker | Separate Python process | 14 | Consumes queue, invokes use cases |

---

## Deployment

| Item | Choice | Phase |
|------|--------|-------|
| Containerization | **Docker** (multi-stage build) | 10, 16 |
| Orchestration | **Kubernetes** | 11, 16 |
| IaC | Terraform or Pulumi (evaluate) | 16 |
| Reverse proxy | Nginx or Traefik | 16 |
| Secrets | K8s Secrets, AWS SSM Parameter Store | 16 |

---

## Testing

| Item | Choice | Phase |
|------|--------|-------|
| Framework | **pytest** | 1 |
| Async tests | **pytest-asyncio** | 1 |
| HTTP testing | **httpx** `AsyncClient` + FastAPI `TestClient` | 1 |
| Mocking | `unittest.mock`, `pytest-mock` | 1 |
| Coverage | **pytest-cov** | 1 |
| Contract tests | Against integration adapter interfaces | 4+ |
| E2E | Playwright (browser), testcontainers (DB) | 8, 16 |

---

## Monitoring

| Item | Choice | Phase |
|------|--------|-------|
| Metrics | **Prometheus** client (`prometheus-fastapi-instrumentator`) | 16 |
| Dashboards | Grafana | 16 |
| Alerting | Prometheus Alertmanager or cloud equivalent | 16 |
| Tracing | OpenTelemetry (evaluate) | 16 |
| Health checks | `/health`, `/ready` endpoints | 1 |

---

## Logging

| Item | Choice | Phase |
|------|--------|-------|
| Library | stdlib **`logging`** | 1 |
| Format | Structured JSON in production; human-readable in dev | 1 |
| Correlation | `X-Correlation-ID` header propagated to all log records | 1 |
| Aggregation | ELK, Loki, or CloudWatch (deployment-specific) | 16 |
| Log levels | DEBUG (dev), INFO (ops), WARNING, ERROR | 1 |

---

## CI/CD

| Item | Choice | Phase |
|------|--------|-------|
| Platform | **GitHub Actions** | 1 |
| Pipeline stages | Lint → Type check → Test → Build → Deploy | 16 |
| Lint | Ruff | 1 |
| Format check | Black `--check` | 1 |
| Type check | Mypy | 1 |
| Image registry | GitHub Container Registry or ECR | 16 |
| Deploy target | K8s cluster (staging → production) | 16 |

---

## Integrations

| Service | Client | Phase |
|---------|--------|-------|
| GitHub | `httpx` (REST + GraphQL) | 9 |
| Docker | `docker` SDK | 10 |
| Kubernetes | Official Python client | 11 |
| AWS | `boto3` | 12 |
| Hostinger | `httpx` (REST API) | 13 |
| Cursor | Extension / webhook (TBD) | 13+ |
| Email | `aiosmtplib` or provider API | Future |

---

## Phase 0 Dependencies (Current)

These are the only approved runtime dependencies today:

```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-dotenv
httpx
```

Dev dependencies (Ruff, Black, Mypy, pytest) will be declared in `pyproject.toml` during Phase 1.

---

## Future Technologies

| Technology | Use Case | Evaluation Trigger |
|------------|----------|-------------------|
| **MCP (Model Context Protocol)** | Standardized tool and context exchange | Phase 17+ or post-16 |
| **OpenTelemetry** | Distributed tracing | Production scale in Phase 16 |
| **Temporal / Celery** | Durable workflow execution | If plan complexity exceeds queue capacity |
| **Qdrant / Weaviate** | Dedicated vector search | pgvector performance insufficient |
| **Local LLM (Ollama, llama.cpp)** | Offline / privacy mode | User demand for local inference |
| **gRPC** | Internal service communication | Multi-service split post-Phase 16 |
| **NATS / Kafka** | High-throughput event bus | Event-driven architecture at scale |
| **WebRTC** | Low-latency voice | WebSocket latency insufficient |

---

## Dependency Approval Process

1. Propose in PR with justification and phase assignment.
2. Update this document and [requirements.txt](requirements.txt) or `pyproject.toml`.
3. No experimental or pre-release versions without explicit approval.
4. Prefer stdlib or already-approved libraries before adding new ones.
