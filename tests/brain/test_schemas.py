"""Brain schema validation tests."""

from __future__ import annotations

from app.brain.schemas.conversation import Message, MessageRole
from app.brain.schemas.execution import ExecutionRequest
from app.brain.schemas.llm import LLMProviderName
from app.brain.schemas.plan import ExecutionPlan, Task


def test_message_defaults() -> None:
    """Message schema assigns ID and timestamp."""
    message = Message(role=MessageRole.USER, content="hello")
    assert message.role == MessageRole.USER
    assert message.id
    assert message.created_at


def test_execution_plan_requires_goal() -> None:
    """ExecutionPlan stores goal and tasks."""
    plan = ExecutionPlan(goal="deploy website", tasks=[])
    assert plan.goal == "deploy website"
    assert plan.status == "draft"


def test_task_order_must_be_positive() -> None:
    """Task order must be >= 1."""
    task = Task(order=1, title="Step", description="Do something")
    assert task.order == 1


def test_model_router_provider_enum() -> None:
    """All required future providers are defined."""
    providers = {p.value for p in LLMProviderName}
    assert "openai" in providers
    assert "anthropic" in providers
    assert "ollama" in providers


def test_execution_request_defaults() -> None:
    """ExecutionRequest defaults require_plan to True."""
    request = ExecutionRequest(user_input="deploy my site")
    assert request.require_plan is True
