# Jarvis OS — System Overview

> **Audience:** New developers joining the team.  
> **Goal:** After reading this document, you should understand what Jarvis OS is, how it is structured, and where to go next.

---

## 1. What Is Jarvis OS?

Jarvis OS is a **Personal AI Operating System**. It is not a chatbot.

A chatbot answers questions and forgets. Jarvis OS:

1. **Understands** goals from text, voice, or screen context
2. **Remembers** preferences, facts, and past outcomes
3. **Plans** multi-step work across tools and environments
4. **Executes** autonomously with safety boundaries
5. **Integrates** with desktop, browser, terminal, cloud, and dev tools

Think of it as an orchestration layer between you and your digital environment — similar to how an OS manages hardware, Jarvis OS manages agents, tools, and workflows.

---

## 2. Core Concepts

| Concept | Definition |
|---------|------------|
| **Agent** | A specialized executor with a role, allowed tools, and policy constraints |
| **Tool** | A bounded capability (run shell command, open URL, deploy container) |
| **Router** | Selects the right model and agent based on user intent |
| **Planner** | Breaks a high-level goal into an ordered graph of steps |
| **Memory** | Persistent store of facts, episodes, and vector embeddings |
| **Plan** | A tracked execution graph with step status and dependencies |
| **Port** | Abstract interface defined in the application layer |
| **Adapter** | Concrete implementation in the infrastructure layer |

---

## 3. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     USER INTERFACES                           │
│         REST API · WebSocket · Voice · Webhooks             │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                   APPLICATION LAYER                           │
│    Use Cases · AI Router · Planner · Agent Orchestrator       │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                      DOMAIN LAYER                             │
│         Entities · Value Objects · Domain Rules               │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                           │
│  LLM · Memory · Tools · Desktop · Browser · Cloud Integrations  │
└──────────────────────────────────────────────────────────────┘
```

**Key rule:** Dependencies flow inward. The domain layer never imports FastAPI, boto3, or Playwright.

Full design details: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 4. How a Request Flows

### Simple chat request (Phase 2+)

```
User → API → Use Case → AI Router → LLM Provider → Response
```

### Autonomous task (Phase 15)

```
User Goal
  → Planner (loads Memory for context)
  → Plan (steps with dependencies)
  → Agent Orchestrator
  → Tool Framework (validate, execute, audit)
  → External systems (GitHub, Docker, desktop, browser, etc.)
  → Memory (store episode)
  → User (completion report)
```

Every step carries a **correlation ID** for tracing across logs.

---

## 5. Repository Layout

```
jarvis-os/
├── src/jarvis/
│   ├── core/           # Config, logging, DI, exceptions
│   ├── domain/         # Business entities and rules (pure Python)
│   ├── application/    # Use cases, ports, orchestration services
│   ├── infrastructure/ # Adapters for external systems
│   └── api/            # FastAPI routes and schemas
├── tests/
├── deploy/             # Docker, K8s manifests (later phases)
└── docs/               # Supplementary documentation
```

| Layer | What goes here | What does NOT go here |
|-------|----------------|------------------------|
| `domain` | `Task`, `Plan`, invariants | HTTP, database drivers |
| `application` | `ExecuteTaskUseCase`, port interfaces | FastAPI routes |
| `infrastructure` | PostgreSQL adapter, Playwright client | Business rules |
| `api` | Route handlers, request/response schemas | Direct SDK calls |

---

## 6. Subsystems at a Glance

| Subsystem | Phase | Purpose |
|-----------|-------|---------|
| Core Backend | 1 | FastAPI app, config, health, DI |
| AI Router | 2 | Intent → model/agent selection |
| Memory | 3 | Long-term and episodic storage |
| Tool Framework | 4 | Register, execute, audit tools |
| Desktop Automation | 5 | Window/input control |
| Voice | 6 | STT/TTS streaming |
| Vision | 7 | Screen capture and analysis |
| Browser Automation | 8 | Playwright-based web control |
| GitHub | 9 | Repos, issues, PRs, CI |
| Docker | 10 | Container management |
| Kubernetes | 11 | Cluster operations |
| AWS | 12 | Cloud resource management |
| Hostinger | 13 | Hosting and DNS |
| Planner | 14 | Goal decomposition |
| Autonomous Execution | 15 | Multi-agent end-to-end runs |
| Production Deployment | 16 | CI/CD, monitoring, runbooks |

Delivery schedule: [ROADMAP.md](ROADMAP.md)

---

## 7. Technology Choices

| Area | Choice |
|------|--------|
| Language | Python 3.12+ |
| API | FastAPI |
| Validation | Pydantic v2 |
| Database | PostgreSQL (Phase 3+) |
| Vector store | pgvector or dedicated store (Phase 3+) |
| Queue | Redis (Phase 14+) |
| Browser | Playwright (Phase 8) |
| Containers | Docker + Kubernetes (Phases 10–11) |

Full stack reference: [TECH_STACK.md](TECH_STACK.md)

---

## 8. Engineering Standards

All code must comply with [CURSOR_RULES.md](CURSOR_RULES.md):

- Python 3.12+, type hints everywhere
- FastAPI, async I/O, Pydantic models
- Clean Architecture with dependency injection
- Ruff + Black + Mypy + pytest before merge
- Secrets in `.env` only — never in source code
- Unit tests required for domain and application layers

Contribution workflow: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 9. Current State

| Item | Status |
|------|--------|
| Documentation | Complete (Phase 0) |
| Application code | Not started |
| API runtime | Phase 1 |
| AI capabilities | Phase 2+ |

**You are here:** Phase 0 → preparing for Phase 1 (Core Backend).

---

## 10. Where to Go Next

| If you want to… | Read… |
|-----------------|-------|
| Understand product vision and requirements | [PROJECT.md](PROJECT.md) |
| Understand system design and data flows | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Know what to build and when | [ROADMAP.md](ROADMAP.md) |
| Pick the right library or service | [TECH_STACK.md](TECH_STACK.md) |
| Submit your first PR | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Write code with AI assistance | [CURSOR_RULES.md](CURSOR_RULES.md) |

---

## 11. Glossary

| Term | Meaning |
|------|---------|
| **Correlation ID** | UUID tracing a request through all subsystems |
| **Approval gate** | Human confirmation required before high-risk tool execution |
| **Episodic memory** | Record of a specific task and its outcome |
| **Semantic memory** | Facts and preferences retrievable by meaning |
| **Plugin** | Externally registered tool conforming to the tool framework schema |
| **MCP** | Model Context Protocol — future standard for tool integration |
