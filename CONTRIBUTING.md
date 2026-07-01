# Jarvis OS — Contributing Guide

> **Audience:** All human and AI contributors.  
> **Prerequisites:** Read [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) and [CURSOR_RULES.md](CURSOR_RULES.md) first.

---

## Getting Started

1. Clone the repository and set up your environment per [README.md](README.md).
2. Read [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) for context.
3. Check [ROADMAP.md](ROADMAP.md) for the current phase — implement only what belongs to that phase.
4. Follow [CURSOR_RULES.md](CURSOR_RULES.md) for all code changes.

---

## Branch Strategy

### Main Branches

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready code; always deployable |
| `develop` | Integration branch (optional; use if team &gt; 2) |

### Feature Branches

```
<type>/<short-description>
```

Examples:

- `feat/phase-1-health-endpoints`
- `fix/memory-retrieval-timeout`
- `docs/architecture-voice-flow`

### Rules

- Branch from `main` (or `develop` if used).
- One feature or fix per branch.
- Keep branches short-lived (≤ 1 week).
- Rebase or merge `main` before opening a PR to avoid conflicts.
- Delete branch after merge.

### Phase Alignment

Branch names should reference the roadmap phase when implementing features:

```
feat/phase-4-tool-registry
```

---

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

### Types

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change without feature/fix |
| `test` | Adding or updating tests |
| `chore` | Build, CI, dependencies |
| `perf` | Performance improvement |

### Examples

```
feat(api): add health and readiness endpoints

docs(architecture): document voice processing flow

fix(memory): handle empty embedding results gracefully

test(tools): add unit tests for tool registry validation
```

### Rules

- Summary line ≤ 72 characters.
- Use imperative mood ("add", not "added").
- One logical change per commit.
- Reference issue numbers in footer when applicable: `Closes #42`.

---

## Code Review Process

### Before Requesting Review

- [ ] Code follows [CURSOR_RULES.md](CURSOR_RULES.md)
- [ ] `ruff check .` passes
- [ ] `black --check .` passes
- [ ] `mypy src` passes
- [ ] `pytest` passes
- [ ] New code has unit tests
- [ ] Public APIs have Google-style docstrings
- [ ] Documentation updated if behavior or architecture changed
- [ ] No secrets, credentials, or `.env` files in the diff

### Review Expectations

| Reviewer checks | Contributor provides |
|-----------------|----------------------|
| Architecture compliance (layer boundaries) | Clear PR description with phase reference |
| Test coverage | Tests for new logic |
| Security (no hardcoded secrets, input validation) | Explanation of any security-sensitive changes |
| Readability and naming | Small, focused diff |
| Documentation | Updated docs for API or behavior changes |

### Approval

- Minimum **1 approval** required for merge.
- Security-sensitive changes (auth, tool permissions, secrets handling) require **2 approvals**.
- Author may not approve their own PR.

---

## Testing Process

### Test Layers

| Layer | Location | What to test |
|-------|----------|-------------|
| Unit | `tests/unit/` | Domain entities, use cases (mocked ports) |
| Integration | `tests/integration/` | Infrastructure adapters, DB, external APIs (mocked or testcontainers) |
| E2E | `tests/e2e/` | Full request flows (later phases) |

### Requirements

- Every new use case → unit test with mocked dependencies.
- Every new adapter → integration test with test double or container.
- Test naming: `test_<what>_<condition>_<expected>`.
- Use `@pytest.mark.asyncio` for async tests.
- Unit tests must not call real external APIs.

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src/jarvis --cov-report=term-missing

# Single file
pytest tests/unit/test_health.py -v
```

### Coverage Targets

| Layer | Minimum coverage |
|-------|-----------------|
| `domain` | 80% |
| `application` | 80% |
| `infrastructure` | 60% |
| `api` | 70% |

---

## Pull Request Process

### 1. Create PR

```bash
git push -u origin feat/phase-1-health-endpoints
```

Open a PR against `main` using the template below.

### 2. PR Title

Same format as commit messages:

```
feat(api): add health and readiness endpoints
```

### 3. PR Description Template

```markdown
## Summary
Brief description of what changed and why.

## Phase
Phase X — <phase name>

## Changes
- Change 1
- Change 2

## Test plan
- [ ] Unit tests added/updated
- [ ] Manual verification steps

## Documentation
- [ ] Updated ARCHITECTURE.md / PROJECT.md / etc. (if applicable)
```

### 4. CI Checks

All PRs must pass:

- Ruff lint
- Black format check
- Mypy type check
- pytest with coverage threshold

### 5. Merge

- Squash merge preferred for feature branches.
- Delete branch after merge.
- Ensure `main` remains deployable.

---

## Documentation Rules

### When to Update Docs

| Change type | Update |
|-------------|--------|
| New subsystem or flow | `ARCHITECTURE.md` |
| New requirement or goal | `PROJECT.md` |
| New dependency or technology | `TECH_STACK.md` |
| Phase completion or scope change | `ROADMAP.md` |
| New coding standard | `CURSOR_RULES.md` |
| New public API endpoint | API docstring + relevant architecture section |
| Onboarding-relevant change | `SYSTEM_OVERVIEW.md` |

### Documentation Standards

- Markdown with clear headings and tables.
- Mermaid diagrams for flows (in `ARCHITECTURE.md`).
- No duplication — link to the canonical document instead of copying content.
- Keep `README.md` as a lightweight index; detail lives in dedicated docs.
- Every feature must have documentation before the PR merges.

### Docstring Standard

Google style for all public modules, classes, and functions:

```python
async def execute_tool(
    tool_name: str,
    params: dict[str, Any],
    *,
    timeout: float = 30.0,
) -> ToolResult:
    """Execute a registered tool with the given parameters.

    Args:
        tool_name: Registered name of the tool to invoke.
        params: Validated input parameters matching the tool schema.
        timeout: Maximum execution time in seconds.

    Returns:
        ToolResult containing output data and execution metadata.

    Raises:
        ToolNotFoundError: If tool_name is not registered.
        ToolExecutionError: If execution fails or times out.
    """
```

---

## Code Deletion Policy

- **Never delete code without explanation** in the PR description.
- If replacing functionality, document what was removed and why.
- If removing dead code, note that tests confirmed it was unused.
- Git history preserves old code — deletion is acceptable when justified.

---

## AI Agent Contributors (Cursor)

AI agents working in this repository must:

1. Read `ARCHITECTURE.md`, `ROADMAP.md`, and `CURSOR_RULES.md` before writing code.
2. Implement only the current phase scope.
3. Create interfaces before adapters.
4. Write tests alongside implementation.
5. Run quality checks before finishing.
6. Update documentation for any public API or architectural change.
7. Not add dependencies without updating `TECH_STACK.md`.
8. Not delete code without explaining why in the commit/PR message.

---

## Getting Help

| Question | Resource |
|----------|----------|
| What is this project? | [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) |
| How should I design this? | [ARCHITECTURE.md](ARCHITECTURE.md) |
| What should I build next? | [ROADMAP.md](ROADMAP.md) |
| What library should I use? | [TECH_STACK.md](TECH_STACK.md) |
| How should I write code? | [CURSOR_RULES.md](CURSOR_RULES.md) |
