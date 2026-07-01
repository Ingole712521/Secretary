"""Long-term memory API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.dependencies import MemoryServiceDep
from app.models.memory import (
    MemoryCreateRequest,
    MemoryFactResponse,
    MemorySearchResponse,
)

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.post(
    "",
    response_model=MemoryFactResponse,
    summary="Store a memory fact",
    description="Persist a fact in long-term memory for future conversations.",
)
async def store_memory(
    request: MemoryCreateRequest,
    memory_service: MemoryServiceDep,
) -> MemoryFactResponse:
    """Store a new memory fact."""
    return await memory_service.store_fact(request)


@router.get(
    "/search",
    response_model=MemorySearchResponse,
    summary="Search memory",
    description="Search long-term memory facts by keyword relevance.",
)
async def search_memory(
    memory_service: MemoryServiceDep,
    q: str = Query(..., min_length=1, max_length=512, description="Search query"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results"),
) -> MemorySearchResponse:
    """Search stored memory facts."""
    return await memory_service.search_facts(q, limit=limit)
