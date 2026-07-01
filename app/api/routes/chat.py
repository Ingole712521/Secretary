"""Chat completion API routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import ChatServiceDep
from app.models.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a chat message",
    description=(
        "Send a user message to the configured LLM provider and return "
        "the assistant response. Does not persist conversation history."
    ),
)
async def create_chat_completion(
    request: ChatRequest,
    chat_service: ChatServiceDep,
) -> ChatResponse:
    """Generate an assistant reply for a user message."""
    return await chat_service.chat(request)
