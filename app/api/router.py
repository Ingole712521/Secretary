"""Aggregate API routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import chat, conversations, health, memory

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(chat.router, prefix="/api/v1")
api_router.include_router(conversations.router, prefix="/api/v1")
api_router.include_router(memory.router, prefix="/api/v1")
