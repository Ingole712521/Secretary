"""Web UI routes for Jarvis voice agent."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["UI"])

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@router.get("/", include_in_schema=False)
async def chat_ui() -> FileResponse:
    """Serve the Jarvis voice chat interface."""
    return FileResponse(_STATIC_DIR / "index.html")
