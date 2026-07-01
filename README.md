# Jarvis OS

**A Personal AI Operating System — not a chatbot.**

Jarvis OS is a production-grade platform that orchestrates voice, memory, planning, multi-agent execution, and deep system integration. It acts as an autonomous layer over your desktop, browser, terminal, cloud infrastructure, and development toolchain.

---

## Project Overview

Jarvis OS is designed to understand intent, plan work, execute across tools and environments, and retain context over time. Unlike conversational assistants, it operates as a full operating layer: routing tasks to specialized agents, invoking tools with strict boundaries, and coordinating long-running workflows with observability and safety controls.

The system is built on **Python 3.12+** and **FastAPI**, following **Clean Architecture** and **SOLID** principles to ensure maintainability as capabilities expand across automation, cloud, and AI domains.

---

## Features

| Domain | Capabilities |
|--------|-------------|
| **Conversation** | Voice-driven interaction with low-latency streaming |
| **Memory** | Long-term semantic and episodic memory with retrieval |
| **Planning** | Task decomposition, dependency graphs, and execution scheduling |
| **Agents** | Multi-agent orchestration with role-based specialization |
| **Desktop** | Window management, input simulation, application control |
| **Browser** | Web navigation, form interaction, and page understanding |
| **Terminal** | Shell command execution with sandboxing and audit logs |
| **Development** | GitHub integration, Cursor IDE hooks, Git workflows |
| **Infrastructure** | Docker, Kubernetes, AWS, and Hostinger management |
| **Files & Email** | File system operations and email automation |
| **Vision** | Screen capture and visual understanding |
| **Autonomy** | End-to-end task execution with human-in-the-loop gates |

---

## Goals

1. **Reliability** — Predictable behavior under failure; graceful degradation and recovery.
2. **Safety** — Explicit permission models, audit trails, and scoped tool access.
3. **Extensibility** — Plugin-style tool framework; new integrations without core changes.
4. **Observability** — Structured logging, tracing, and metrics across all subsystems.
5. **Performance** — Async-first I/O; sub-second routing for common operations.
6. **Privacy** — Local-first options; secrets never committed; environment-driven config.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.12+ |
| API Framework | FastAPI |
| Validation | Pydantic v2 |
| Configuration | pydantic-settings, python-dotenv |
| HTTP Client | httpx (async) |
| Linting | Ruff |
| Formatting | Black |
| Type Checking | Mypy |
| Testing | pytest, pytest-asyncio |
| Containerization | Docker (Phase 10+) |

---

## Installation

### Prerequisites

- Python 3.12 or later
- Git
- A virtual environment tool (`venv` or `uv`)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd jarvis-os

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your local values (never commit .env)
```

### Verify Installation

```bash
# Run linting (once dev tooling is configured)
ruff check .

# Run type checking (once application code exists)
mypy .

# Run tests (once test suite exists)
pytest
```

---

## Development Workflow

1. **Read the docs** — Start with [PROJECT.md](PROJECT.md) and [ARCHITECTURE.md](ARCHITECTURE.md) before writing code.
2. **Follow phases** — Implement features according to [ROADMAP.md](ROADMAP.md); do not skip foundational phases.
3. **Adhere to rules** — All code must comply with [CURSOR_RULES.md](CURSOR_RULES.md).
4. **Branch strategy** — Use feature branches; keep `main` deployable.
5. **Environment** — Use `.env` for local secrets; reference `.env.example` for required variables.
6. **Quality gates** — Ruff, Black, and Mypy must pass before merge.
7. **No business logic in foundation** — Phase 0 establishes structure and docs only; application code begins in Phase 1.

### Repository Layout (Planned)

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full folder structure and module responsibilities.

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| [PROJECT.md](PROJECT.md) | Vision, requirements, milestones, risks |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, patterns, communication flow |
| [ROADMAP.md](ROADMAP.md) | Phased development plan |
| [CURSOR_RULES.md](CURSOR_RULES.md) | Coding standards for contributors and AI agents |

---

## License

License to be determined. See repository maintainers for usage terms.

---

## Status

**Phase 0 — Project Foundation** — Documentation and project scaffolding only. No application runtime yet.
# Secretary
