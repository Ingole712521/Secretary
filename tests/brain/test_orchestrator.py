"""Brain orchestrator architecture tests."""

from __future__ import annotations

import pytest

from app.brain.factory import build_brain
from app.brain.schemas.execution import ExecutionRequest, ExecutionStatus
from app.config.settings import Environment, Settings


@pytest.fixture
def brain_settings() -> Settings:
    """Settings for Brain subsystem tests."""
    return Settings(
        _env_file=None,
        app_env=Environment.TESTING,
        api_secret_key="test-secret",  # noqa: S106
    )


@pytest.fixture
def brain(brain_settings: Settings):
    """Brain container for tests."""
    return build_brain(brain_settings)


@pytest.mark.asyncio
async def test_orchestrator_generates_plan(brain) -> None:
    """Orchestrator returns a planned result with tasks."""
    request = ExecutionRequest(user_input="Deploy my website")
    result = await brain.orchestrator.execute(request)

    assert result.status == ExecutionStatus.PLANNED
    assert result.plan is not None
    assert result.conversation_id is not None
    assert len(result.plan.tasks) >= 1
    assert result.plan.goal == "Deploy my website"


@pytest.mark.asyncio
async def test_orchestrator_tracks_conversation(brain) -> None:
    """Orchestrator creates and updates a conversation."""
    request = ExecutionRequest(user_input="Hello Jarvis")
    result = await brain.orchestrator.execute(request)

    conversation = await brain.conversation_manager.get_or_create(
        result.conversation_id,
    )
    assert len(conversation.messages) >= 1
    assert conversation.messages[0].content == "Hello Jarvis"


@pytest.mark.asyncio
async def test_model_router_selects_without_provider_call(brain) -> None:
    """ModelRouter returns metadata without registered providers."""
    model = brain.model_router.select_model()
    assert model.provider
    assert model.model_id


@pytest.mark.asyncio
async def test_get_provider_raises_when_not_registered(brain) -> None:
    """ModelRouter raises when no adapter is registered."""
    from app.brain.exceptions import ModelRoutingError
    from app.brain.schemas.llm import LLMProviderName

    with pytest.raises(ModelRoutingError):
        brain.model_router.get_provider(LLMProviderName.OPENAI)
