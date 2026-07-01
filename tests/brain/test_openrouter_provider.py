"""OpenRouter provider unit tests."""

from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from app.brain.exceptions import LLMCompletionError, LLMProviderError
from app.brain.providers.openrouter import OpenRouterProvider
from app.brain.schemas.conversation import Message, MessageRole
from app.brain.schemas.llm import (
    LLMProviderName,
    LLMRequest,
    ModelCapability,
    ModelInfo,
)
from app.config.settings import Settings
from app.exceptions import ConfigurationException


def _openrouter_settings(**overrides: object) -> Settings:
    """Build settings configured for OpenRouter."""
    defaults: dict[str, object] = {
        "_env_file": None,
        "llm_provider": "openrouter",
        "openrouter_api_key": "sk-or-test-key",
        "openrouter_model": "anthropic/claude-3.5-sonnet",
        "openrouter_api_base": "https://openrouter.ai/api/v1",
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def _mock_client(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.AsyncClient:
    """Create an async HTTP client with a mock transport."""
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _completion_handler(request: httpx.Request) -> httpx.Response:
    """Return a successful chat completion response."""
    assert request.url.path.endswith("/chat/completions")
    assert request.headers["Authorization"] == "Bearer sk-or-test-key"
    return httpx.Response(
        200,
        json={
            "id": "gen-123",
            "model": "anthropic/claude-3.5-sonnet",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello from OpenRouter",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        },
    )


@pytest.mark.asyncio
async def test_openrouter_complete_returns_parsed_response() -> None:
    """complete() maps OpenRouter responses to LLMResponse."""
    settings = _openrouter_settings()
    provider = OpenRouterProvider(
        settings,
        http_client=_mock_client(_completion_handler),
    )

    request = LLMRequest(
        model=ModelInfo(
            provider=LLMProviderName.OPENROUTER,
            model_id="anthropic/claude-3.5-sonnet",
            display_name="Claude 3.5 Sonnet",
            capabilities=[ModelCapability.CHAT],
        ),
        messages=[Message(role=MessageRole.USER, content="Hi")],
    )

    response = await provider.complete(request)

    assert response.content == "Hello from OpenRouter"
    assert response.model.model_id == "anthropic/claude-3.5-sonnet"
    assert response.finish_reason == "stop"
    assert response.usage["total_tokens"] == 15


@pytest.mark.asyncio
async def test_openrouter_complete_raises_without_api_key() -> None:
    """complete() raises ConfigurationException when no API key is set."""
    settings = _openrouter_settings(openrouter_api_key=None)
    provider = OpenRouterProvider(
        settings,
        http_client=_mock_client(_completion_handler),
    )
    request = LLMRequest(
        model=ModelInfo(
            provider=LLMProviderName.OPENROUTER,
            model_id="openrouter/auto",
            display_name="Auto",
            capabilities=[ModelCapability.CHAT],
        ),
        messages=[Message(role=MessageRole.USER, content="Hi")],
    )

    with pytest.raises(ConfigurationException, match="API key"):
        await provider.complete(request)


@pytest.mark.asyncio
async def test_openrouter_complete_raises_on_http_error() -> None:
    """complete() raises LLMCompletionError for provider HTTP errors."""

    def error_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"message": "Invalid API key"}},
        )

    settings = _openrouter_settings()
    provider = OpenRouterProvider(
        settings,
        http_client=_mock_client(error_handler),
    )
    request = LLMRequest(
        model=ModelInfo(
            provider=LLMProviderName.OPENROUTER,
            model_id="openrouter/auto",
            display_name="Auto",
            capabilities=[ModelCapability.CHAT],
        ),
        messages=[Message(role=MessageRole.USER, content="Hi")],
    )

    with pytest.raises(LLMCompletionError, match="Invalid API key"):
        await provider.complete(request)


@pytest.mark.asyncio
async def test_openrouter_complete_raises_on_transport_error() -> None:
    """complete() raises LLMProviderError when the HTTP transport fails."""

    def failing_handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    settings = _openrouter_settings()
    provider = OpenRouterProvider(
        settings,
        http_client=_mock_client(failing_handler),
    )
    request = LLMRequest(
        model=ModelInfo(
            provider=LLMProviderName.OPENROUTER,
            model_id="openrouter/auto",
            display_name="Auto",
            capabilities=[ModelCapability.CHAT],
        ),
        messages=[Message(role=MessageRole.USER, content="Hi")],
    )

    with pytest.raises(LLMProviderError, match="request failed"):
        await provider.complete(request)


@pytest.mark.asyncio
async def test_openrouter_health_check_success() -> None:
    """health_check() returns True when models endpoint succeeds."""

    def models_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/models")
        return httpx.Response(200, json={"data": []})

    settings = _openrouter_settings()
    provider = OpenRouterProvider(
        settings,
        http_client=_mock_client(models_handler),
    )

    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_openrouter_list_models_parses_catalog() -> None:
    """list_models() parses model metadata from the provider catalog."""

    def models_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "anthropic/claude-3.5-sonnet",
                        "name": "Claude 3.5 Sonnet",
                        "context_length": 200000,
                    }
                ]
            },
        )

    settings = _openrouter_settings()
    provider = OpenRouterProvider(
        settings,
        http_client=_mock_client(models_handler),
    )

    models = await provider.list_models()

    assert len(models) == 1
    assert models[0].model_id == "anthropic/claude-3.5-sonnet"
    assert models[0].context_window == 200000
