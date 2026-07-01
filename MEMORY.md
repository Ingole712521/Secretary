# Long-Term Memory — Jarvis OS Sprint 7

> Jarvis remembers facts about you across conversations and sessions.

---

## Overview

Sprint 7 adds **long-term memory** separate from conversation session history:

| Layer | Scope | Storage |
|-------|--------|---------|
| **Conversation** (Sprint 4) | Current chat thread | In-memory per process |
| **Memory** (Sprint 7) | Facts across sessions | SQLite at `data/memory.db` |

```
POST /api/v1/memory  →  SQLite  →  injected into chat system prompt
GET  /api/v1/memory/search
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MEMORY_ENABLED` | `true` | Inject memories into chat |
| `MEMORY_DB_PATH` | `data/memory.db` | SQLite database path |
| `MEMORY_SEARCH_LIMIT` | `10` | Default API search limit |
| `MEMORY_CONTEXT_LIMIT` | `5` | Max facts injected per chat turn |

---

## API

### Store a fact

**POST /api/v1/memory**

```json
{
  "content": "User's name is Nehal",
  "category": "personal",
  "tags": ["name", "identity"]
}
```

### Search memory

**GET /api/v1/memory/search?q=Nehal&limit=10**

```json
{
  "query": "Nehal",
  "results": [
    {
      "id": "...",
      "content": "User's name is Nehal",
      "score": 3.5,
      "tags": ["name"],
      "updated_at": "..."
    }
  ]
}
```

---

## Chat integration

When you send a chat message, Jarvis:

1. Searches memory for facts relevant to your message (keyword scoring)
2. Injects top matches as a system message:

```
Known facts about the user:
- User's name is Nehal
```

3. Sends conversation history + memories to the LLM

### Example workflow

```bash
# 1. Store a fact
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{"content": "My name is Nehal"}'

# 2. Start a new conversation and ask
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my name?"}'
```

---

## Architecture

```
app/memory/
├── interfaces/memory_store.py    # Port
├── stores/sqlite_store.py        # SQLite adapter
├── schemas/models.py             # MemoryFact, MemorySearchResult
├── search.py                     # Keyword relevance scoring
└── factory.py                    # build_memory_store()

app/services/memory.py            # MemoryService
app/api/routes/memory.py          # HTTP routes
```

---

## Search (Sprint 7)

Sprint 7 uses **keyword relevance scoring** (not vector embeddings). Future sprints may add semantic search with embeddings.

---

## Testing

```bash
python -m pytest tests/memory/ tests/test_memory_api.py tests/test_chat_memory.py -v
```

---

## Next sprint

**Sprint 8 — Voice** (mic + speaker). Say **"start sprint 8"** when ready.
