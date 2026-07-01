"""Conversation session API routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import ConversationServiceDep
from app.models.conversation import ConversationDetail, ConversationSummary

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get(
    "",
    response_model=list[ConversationSummary],
    summary="List conversations",
    description="Return all conversation sessions, newest first.",
)
async def list_conversations(
    conversation_service: ConversationServiceDep,
) -> list[ConversationSummary]:
    """List conversation sessions."""
    return await conversation_service.list_conversations()


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get conversation",
    description="Return a conversation with full message history.",
)
async def get_conversation(
    conversation_id: str,
    conversation_service: ConversationServiceDep,
) -> ConversationDetail:
    """Return conversation detail."""
    return await conversation_service.get_conversation(conversation_id)
