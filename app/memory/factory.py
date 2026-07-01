"""Memory subsystem factory."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.memory.stores.sqlite_store import SqliteMemoryStore

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.memory.interfaces.memory_store import MemoryStore


def build_memory_store(settings: Settings) -> MemoryStore:
    """Construct the configured memory store adapter.

    Args:
        settings: Application settings.

    Returns:
        SQLite memory store at the configured path.
    """
    db_path = settings.memory_db_path or (settings.data_dir / "memory.db")
    return SqliteMemoryStore(Path(db_path))
