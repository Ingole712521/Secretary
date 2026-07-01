# Jarvis OS — Development Roadmap

> **Audience:** Engineering leads and contributors planning delivery.  
> **Rule:** Do not skip phases. Each phase produces a shippable increment.

**Complexity legend:** Low · Medium · High · Very High

---

## Phase Dependency Graph

```
Phase 0 → Phase 1 → Phase 2 ──┬── Phase 3
                               └── Phase 4 ──┬── Phases 5–13 (parallel tracks)
                                              └── Phase 14 → Phase 15 → Phase 16
```

---

## Phase 0 — Project Foundation

| Field | Detail |
|-------|--------|
| **Status** | Complete |
| **Goal** | Establish documentation, standards, and configuration without application code |
| **Complexity** | Low |
| **Dependencies** | None |

### Deliverables

- Project documentation (README, PROJECT, ARCHITECTURE, ROADMAP, CURSOR_RULES, TECH_STACK, CONTRIBUTING, SYSTEM_OVERVIEW)
- `.env.example`, `.gitignore`, `requirements.txt`
- Approved engineering standards

### Acceptance Criteria

- [x] All foundation documents complete and internally consistent
- [x] Dev environment reproducible from README
- [x] No application runtime code exists
- [x] Documentation index in README links to all docs

---

## Phase 1 — Core Backend

| Field | Detail |
|-------|--------|
| **Goal** | Runnable FastAPI application with configuration, logging, DI, and health endpoints |
| **Complexity** | Medium |
| **Dependencies** | Phase 0 |

### Deliverables

- `src/jarvis/` package skeleton per ARCHITECTURE.md
- `pyproject.toml` (Ruff, Black, Mypy, pytest)
- `create_app()` factory with lifespan hooks
- `Settings` via pydantic-settings
- Structured logging with correlation ID middleware
- `GET /health`, `GET /ready` endpoints
- Global exception handler with error envelope
- DI container in `core/dependencies.py`
- Unit tests for config, health routes, and exception handling

### Acceptance Criteria

- [ ] `uvicorn jarvis.main:app` starts without errors
- [ ] `/health` returns 200 with `{ "status": "ok" }`
- [ ] `/ready` returns 200 when app is initialized
- [ ] Correlation ID present in logs and response headers
- [ ] Ruff, Black, Mypy pass in CI
- [ ] Unit test coverage ≥ 80% for implemented modules

---

## Phase 2 — AI Router

| Field | Detail |
|-------|--------|
| **Goal** | Route user requests to appropriate models and agents based on intent |
| **Complexity** | High |
| **Dependencies** | Phase 1 |

### Deliverables

- `LLMProvider` port interface
- At least one provider adapter (OpenAI-compatible)
- Intent classifier (rule-based or LLM-assisted)
- `RouterService` with model selection and fallback chain
- `ChatUseCase` and `POST /v1/chat` endpoint
- Provider swappable via environment configuration

### Acceptance Criteria

- [ ] Router selects correct agent for ≥ 5 test intent categories
- [ ] Provider swap requires only config change, no code change
- [ ] Fallback chain activates when primary provider fails
- [ ] Integration tests with mocked LLM pass
- [ ] API documented with OpenAPI summary and response models

---

## Phase 3 — Memory

| Field | Detail |
|-------|--------|
| **Goal** | Persistent long-term and episodic memory with semantic retrieval |
| **Complexity** | High |
| **Dependencies** | Phase 1, Phase 2 |

### Deliverables

- Memory entities: `Fact`, `Episode`, `Embedding` value objects
- `MemoryStore` port interface
- PostgreSQL + pgvector adapter (SQLite for local dev)
- Embedding generation via configured provider
- `StoreMemoryUseCase`, `QueryMemoryUseCase`
- `POST /v1/memory`, `GET /v1/memory/search` endpoints
- Alembic migrations

### Acceptance Criteria

- [ ] Memories persist across application restarts
- [ ] Semantic search returns relevant results in ≥ 3 test scenarios
- [ ] Memory writes and reads appear in audit log
- [ ] Embedding failures degrade gracefully with clear error
- [ ] Unit tests for domain entities; integration tests for adapter

---

## Phase 4 — Tool Framework

| Field | Detail |
|-------|--------|
| **Goal** | Register, validate, execute, and audit tools with permission scopes |
| **Complexity** | High |
| **Dependencies** | Phase 1 |

### Deliverables

- Tool registry with JSON Schema validation
- `ToolExecutor` port and async implementation (timeout, retry)
- Permission model scoped per agent role
- Audit log for all invocations (correlation ID, duration, outcome)
- Built-in tools: `echo`, `get_time`
- Plugin loader stub in `infrastructure/plugins/`
- `InvokeToolUseCase` and tool management API

### Acceptance Criteria

- [ ] Tools registered dynamically at startup and via API
- [ ] Invalid tool inputs rejected with validation error
- [ ] Audit log queryable by correlation ID and tool name
- [ ] Permission denied for out-of-scope tool access
- [ ] Unit tests for registry, executor, and permission model

---

## Phase 5 — Desktop Automation

| Field | Detail |
|-------|--------|
| **Goal** | Control desktop environment (windows, input, applications) |
| **Complexity** | High |
| **Dependencies** | Phase 4 |

### Deliverables

- `DesktopAutomation` port interface
- Windows adapter (primary platform)
- macOS and Linux stubs with graceful unsupported response
- Tools: `focus_window`, `click`, `type_text`, `screenshot_region`
- Approval gate integration for high-risk actions
- Platform detection at startup

### Acceptance Criteria

- [ ] Window focus and input simulation work on Windows
- [ ] Tools registered in tool framework and audited
- [ ] Unsupported platform returns clear error, not crash
- [ ] Destructive actions require approval when configured
- [ ] Integration tests with mocked OS APIs

---

## Phase 6 — Voice

| Field | Detail |
|-------|--------|
| **Goal** | Voice input and output for hands-free interaction |
| **Complexity** | Very High |
| **Dependencies** | Phase 2, Phase 4 |

### Deliverables

- `SpeechToText` and `TextToSpeech` port interfaces
- STT adapter (Whisper API or local)
- TTS adapter
- WebSocket endpoint for real-time audio streaming
- Voice session linked to chat pipeline
- Latency benchmarks documented

### Acceptance Criteria

- [ ] End-to-end voice turn: speak → transcript → response → audio
- [ ] Partial transcripts streamed during speech
- [ ] Fallback to text when voice services unavailable
- [ ] Voice session tied to conversation session ID
- [ ] Audio not persisted by default

---

## Phase 7 — Vision

| Field | Detail |
|-------|--------|
| **Goal** | Screen understanding via capture and visual analysis |
| **Complexity** | High |
| **Dependencies** | Phase 2, Phase 4 |

### Deliverables

- Screen capture adapter (full screen and region)
- `VisionAnalyzer` port interface
- Multimodal LLM adapter for image analysis
- Tools: `describe_screen`, `find_element`
- Optional PII redaction before analysis
- Vision context fed to planner and agents

### Acceptance Criteria

- [ ] Screen described accurately in ≥ 3 test scenarios
- [ ] Vision tools available via tool framework
- [ ] PII redaction option documented and testable
- [ ] Captured images not persisted unless configured

---

## Phase 8 — Browser Automation

| Field | Detail |
|-------|--------|
| **Goal** | Navigate and interact with web pages programmatically |
| **Complexity** | High |
| **Dependencies** | Phase 4 |

### Deliverables

- `BrowserAutomation` port interface
- Playwright adapter (headless and headed)
- Tools: `navigate`, `click`, `fill`, `extract_text`, `screenshot`
- Browser context lifecycle management
- Domain allowlist via configuration
- Session cleanup on timeout

### Acceptance Criteria

- [ ] Navigate and extract content from test HTML pages
- [ ] Tools registered, permission-scoped, and audited
- [ ] Browser contexts cleaned up after task completion or timeout
- [ ] Domain allowlist blocks unauthorized navigation
- [ ] Integration tests with local test server

---

## Phase 9 — GitHub

| Field | Detail |
|-------|--------|
| **Goal** | Manage repositories, issues, pull requests, and Actions |
| **Complexity** | Medium |
| **Dependencies** | Phase 4 |

### Deliverables

- `GitHubClient` port interface
- REST + GraphQL adapter via httpx
- Tools: `list_repos`, `create_issue`, `open_pr`, `check_ci_status`
- PAT / GitHub App auth via environment variables
- Rate limit handling

### Acceptance Criteria

- [ ] CRUD on issues in a test repository
- [ ] Rate limit responses handled with backoff
- [ ] Credentials never appear in logs
- [ ] Contract tests against mocked GitHub API

---

## Phase 10 — Docker

| Field | Detail |
|-------|--------|
| **Goal** | Manage containers, images, and compose stacks |
| **Complexity** | Medium |
| **Dependencies** | Phase 4 |

### Deliverables

- `DockerClient` port interface
- Docker SDK adapter
- Tools: `list_containers`, `build_image`, `run_container`, `get_logs`
- No privileged container mode by default
- Socket/context scoped via configuration

### Acceptance Criteria

- [ ] Start and stop container in test environment
- [ ] Build image from Dockerfile
- [ ] Privileged mode disabled by default
- [ ] All operations audited

---

## Phase 11 — Kubernetes

| Field | Detail |
|-------|--------|
| **Goal** | Operate Kubernetes clusters and workloads |
| **Complexity** | High |
| **Dependencies** | Phase 4, Phase 10 |

### Deliverables

- `KubernetesClient` port interface
- Official Python K8s client adapter
- Tools: `get_pods`, `apply_manifest`, `scale_deployment`, `get_logs`
- Namespace-scoped RBAC
- kubeconfig from environment only

### Acceptance Criteria

- [ ] Deploy test workload to dev cluster
- [ ] Read pod status and logs
- [ ] No cluster-admin permissions by default
- [ ] Mutating operations require approval gate

---

## Phase 12 — AWS

| Field | Detail |
|-------|--------|
| **Goal** | Manage AWS resources (EC2, S3, Lambda, IAM read) |
| **Complexity** | High |
| **Dependencies** | Phase 4 |

### Deliverables

- Service-specific port interfaces (S3, EC2, Lambda)
- boto3 adapter with async wrappers
- Tools: `s3_list`, `s3_upload`, `ec2_describe`, `lambda_invoke`
- IAM least-privilege enforcement
- Region locked via configuration

### Acceptance Criteria

- [ ] S3 and EC2 read operations in test account
- [ ] Mutating operations require approval gate
- [ ] Credentials via env or instance role only
- [ ] Region cannot be overridden at runtime

---

## Phase 13 — Hostinger

| Field | Detail |
|-------|--------|
| **Goal** | Manage Hostinger hosting, domains, and VPS |
| **Complexity** | Medium |
| **Dependencies** | Phase 4 |

### Deliverables

- `HostingerClient` port interface
- REST API adapter via httpx
- Tools: `list_domains`, `get_dns_records`, `get_vps_status`
- API token via environment variable
- Rate limit and error handling

### Acceptance Criteria

- [ ] List domains and DNS in test account
- [ ] Destructive DNS changes require approval
- [ ] API errors mapped to domain exceptions
- [ ] Token never logged

---

## Phase 14 — Planner

| Field | Detail |
|-------|--------|
| **Goal** | Decompose goals into executable plans with dependency tracking |
| **Complexity** | Very High |
| **Dependencies** | Phase 2, Phase 3, Phase 4 |

### Deliverables

- `Plan` entity with steps, dependencies, and status
- `PlannerService` with LLM-assisted decomposition
- `PlanRepository` for persistence and resume
- Redis queue for async step dispatch
- API: create plan, get status, cancel
- Integration with agent orchestrator (stub)

### Acceptance Criteria

- [ ] Multi-step plan generated from natural language goal
- [ ] Plan state survives application restart
- [ ] Failed steps trigger configurable retry or escalation
- [ ] Independent steps identified for parallel execution
- [ ] Planner uses memory context in decomposition

---

## Phase 15 — Autonomous Execution

| Field | Detail |
|-------|--------|
| **Goal** | End-to-end autonomous task execution with human-in-the-loop |
| **Complexity** | Very High |
| **Dependencies** | Phase 14, Phases 5–13 (tool integrations) |

### Deliverables

- `AgentOrchestrator` with multi-agent dispatch and context handoff
- `ExecutionEngine` for plan step scheduling
- Approval gates for high-risk operations
- Real-time progress via WebSocket
- Compensating rollback actions where possible
- Full audit trail from goal to completion

### Acceptance Criteria

- [ ] Low-risk multi-tool task completes without manual intervention
- [ ] High-risk operations pause and await user approval
- [ ] Progress events streamed in real time
- [ ] Full audit trail queryable by plan ID
- [ ] Failed plan reports actionable error summary

---

## Phase 16 — Production Deployment

| Field | Detail |
|-------|--------|
| **Goal** | Deploy Jarvis OS to production with monitoring and operations runbooks |
| **Complexity** | Very High |
| **Dependencies** | Phase 15 |

### Deliverables

- Multi-stage production Dockerfile
- Docker Compose and Kubernetes manifests
- GitHub Actions CI/CD pipeline (lint → test → build → deploy)
- Prometheus metrics and Grafana dashboards
- Alerting rules for critical failures
- Operations runbooks (incident, backup, upgrade)
- TLS, secrets management, network policies
- Staging and production environments

### Acceptance Criteria

- [ ] Deployed to staging and production
- [ ] SLOs defined: availability ≥ 99.5%, health p95 &lt; 100 ms
- [ ] Disaster recovery tested (DB backup restore)
- [ ] Runbooks reviewed by operator
- [ ] Security hardening checklist complete
- [ ] Zero secrets in container images or logs

---

## Timeline Estimates

| Phase | Complexity | Duration | Cumulative |
|-------|-----------|----------|------------|
| 0 | Low | 1 week | 1 week |
| 1 | Medium | 2 weeks | 3 weeks |
| 2 | High | 2 weeks | 5 weeks |
| 3 | High | 3 weeks | 8 weeks |
| 4 | High | 2 weeks | 10 weeks |
| 5 | High | 3 weeks | 13 weeks |
| 6 | Very High | 3 weeks | 16 weeks |
| 7 | High | 3 weeks | 19 weeks |
| 8 | High | 3 weeks | 22 weeks |
| 9 | Medium | 2 weeks | 24 weeks |
| 10 | Medium | 2 weeks | 26 weeks |
| 11 | High | 2 weeks | 28 weeks |
| 12 | High | 2 weeks | 30 weeks |
| 13 | Medium | 2 weeks | 32 weeks |
| 14 | Very High | 4 weeks | 36 weeks |
| 15 | Very High | 4 weeks | 40 weeks |
| 16 | Very High | 3 weeks | 43 weeks |

*Estimates assume a team of 1–3 developers. Phases 5–13 can overlap after Phase 4 completes.*

---

## Parallel Tracks (After Phase 4)

Once the tool framework is stable, these phases can proceed in parallel:

```
Track A: Phase 5 (Desktop) → Phase 7 (Vision)
Track B: Phase 6 (Voice)
Track C: Phase 8 (Browser)
Track D: Phases 9–13 (Integrations)
```

All tracks must complete before Phase 15 (Autonomous Execution).

---

## Current Focus

**Phase 0 — Complete.** Next: **Phase 1 — Core Backend**.

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to start implementing.
