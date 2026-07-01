# Jarvis OS

**A Personal AI Operating System — not a chatbot.**

Jarvis OS is a production-grade platform that orchestrates voice, memory, planning, multi-agent execution, and deep system integration. It acts as an autonomous layer over your desktop, browser, terminal, cloud infrastructure, and development toolchain.

---

## Quick Start

### Prerequisites

- Python 3.12+
- Git
- `venv` or `uv`

### Setup

```bash
git clone <repository-url>
cd jarvis-os

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Edit .env locally — never commit it
```

### Verify (after Phase 1)

```bash
ruff check .
black --check .
mypy src
pytest
```

---

## What Jarvis OS Does

| Capability | Description |
|------------|-------------|
| Voice | Hands-free interaction with streaming STT/TTS |
| Memory | Long-term semantic and episodic context |
| Planning | Goal decomposition and execution scheduling |
| Agents | Multi-agent orchestration with role specialization |
| Automation | Desktop, browser, and terminal control |
| Integrations | GitHub, Docker, Kubernetes, AWS, Hostinger, Cursor |
| Autonomy | End-to-end task execution with approval gates |

For a full system explanation, start with [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md).

---

## Documentation

| Document | Audience | Purpose |
|----------|----------|---------|
| [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | New developers | Bird's-eye view of the entire system |
| [PROJECT.md](PROJECT.md) | Product & engineering | Vision, requirements, goals, risks |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Engineers | Design, flows, patterns, strategies |
| [ROADMAP.md](ROADMAP.md) | Engineering leads | Phased delivery plan |
| [TECH_STACK.md](TECH_STACK.md) | Engineers & ops | Technology choices by domain |
| [CURSOR_RULES.md](CURSOR_RULES.md) | All contributors | Mandatory coding standards |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributors | Branching, PRs, reviews, testing |

---

## Development

1. Read [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) and [ARCHITECTURE.md](ARCHITECTURE.md).
2. Implement only the current phase in [ROADMAP.md](ROADMAP.md).
3. Follow [CURSOR_RULES.md](CURSOR_RULES.md) and [CONTRIBUTING.md](CONTRIBUTING.md).
4. See [TECH_STACK.md](TECH_STACK.md) before adding dependencies.

---

## Status

**Phase 0 — Project Foundation** — Documentation and configuration only. Application code begins in Phase 1.

---

## License

License to be determined. Contact repository maintainers for usage terms.
