"""OpenRouter LLM provider adapter."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.brain.exceptions import LLMCompletionError, LLMProviderError
from app.brain.schemas.conversation import Message
from app.brain.schemas.llm import (
    LLMProviderName,
    LLMRequest,
    LLMResponse,
    ModelCapability,
    ModelInfo,
)
from app.config.settings import Settings
from app.constants import LOGGER_LLM
from app.exceptions import ConfigurationException

logger = logging.getLogger(LOGGER_LLM)

_DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class OpenRouterProvider:
    """OpenRouter adapter implementing the ``LLMProvider`` port.

    Reads API key and base URL from application settings. Uses the
    OpenAI-compatible ``/chat/completions`` endpoint.

    Attributes:
        _settings: Application configuration.
        _http_client: Injected HTTP client, or None to create one lazily.
        _owned_client: Internally created client when none is injected.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the OpenRouter provider.

        Args:
            settings: Application settings with API key and base URL.
            http_client: Optional HTTP client for testing or shared use.
        """
        self._settings = settings
        self._http_client = http_client
        self._owned_client: httpx.AsyncClient | None = None

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        return LLMProviderName.OPENROUTER.value

    async def close(self) -> None:
        """Close the internally owned HTTP client, if any."""
        if self._owned_client is not None:
            await self._owned_client.aclose()
            self._owned_client = None

    async def list_models(self) -> list[ModelInfo]:
        """List models available from OpenRouter.

        Fetches the provider catalog when credentials are configured.
        Falls back to the configured default model when the request fails.

        Returns:
            List of model metadata objects.
        """
        api_key = self._require_api_key()
        url = f"{self._base_url()}/models"

        try:
            client = await self._get_client()
            response = await client.get(
                url,
                headers=self._auth_headers(api_key),
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning(
                "OpenRouter model listing failed; using configured default: %s",
                exc,
            )
            return [self._default_model_info()]

        payload = response.json()
        models: list[ModelInfo] = []
        for entry in payload.get("data", []):
            model_id = entry.get("id")
            if not model_id:
                continue
            models.append(
                ModelInfo(
                    provider=LLMProviderName.OPENROUTER,
                    model_id=model_id,
                    display_name=entry.get("name", model_id),
                    capabilities=[ModelCapability.CHAT],
                    context_window=entry.get("context_length"),
                    metadata={"pricing": entry.get("pricing", {})},
                )
            )
        return models or [self._default_model_info()]

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a chat completion via OpenRouter.

        Args:
            request: Structured LLM request payload.

        Returns:
            Structured LLM response with generated content.

        Raises:
            ConfigurationException: When the API key is missing.
            LLMCompletionError: When the provider returns an error response.
            LLMProviderError: When the HTTP request fails.
        """
        api_key = self._require_api_key()
        url = f"{self._base_url()}/chat/completions"
        body = self._build_completion_body(request)

        logger.info(
            "OpenRouter completion request | model=%s messages=%d",
            body["model"],
            len(body["messages"]),
        )

        try:
            client = await self._get_client()
            response = await client.post(
                url,
                headers=self._auth_headers(api_key),
                json=body,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._extract_error_detail(exc.response)
            logger.error(
                "OpenRouter completion HTTP error | status=%s detail=%s",
                exc.response.status_code,
                detail,
            )
            raise LLMCompletionError(
                f"OpenRouter completion failed: {detail}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("OpenRouter completion transport error: %s", exc)
            raise LLMProviderError(
                f"OpenRouter request failed: {exc}",
            ) from exc

        payload = response.json()
        return self._parse_completion_response(payload, request.model)

    async def health_check(self) -> bool:
        """Check whether OpenRouter is reachable with configured credentials.

        Returns:
            True when the provider responds successfully to a models request.
        """
        if not self._settings.has_llm_credentials:
            return False

        api_key = self._settings.get_active_llm_api_key()
        if api_key is None:
            return False

        url = f"{self._base_url()}/models"
        try:
            client = await self._get_client()
            response = await client.get(
                url,
                headers=self._auth_headers(api_key.get_secret_value()),
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return False
        return True

    def _require_api_key(self) -> str:
        """Return the active API key or raise when missing."""
        api_key = self._settings.get_active_llm_api_key()
        if api_key is None:
            msg = "OpenRouter API key is not configured"
            raise ConfigurationException(msg)
        return api_key.get_secret_value()

    def _base_url(self) -> str:
        """Return the OpenRouter API base URL without a trailing slash."""
        return self._settings.openrouter_api_base.rstrip("/")

    async def _get_client(self) -> httpx.AsyncClient:
        """Return the injected or lazily created HTTP client."""
        if self._http_client is not None:
            return self._http_client
        if self._owned_client is None:
            self._owned_client = httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
        return self._owned_client

    def _auth_headers(self, api_key: str) -> dict[str, str]:
        """Build authorization headers for OpenRouter requests."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://jarvis-os.local",
            "X-Title": self._settings.app_name,
        }

    def _default_model_info(self) -> ModelInfo:
        """Return metadata for the configured default OpenRouter model."""
        model_id = self._settings.get_active_llm_model()
        return ModelInfo(
            provider=LLMProviderName.OPENROUTER,
            model_id=model_id,
            display_name=model_id,
            capabilities=[ModelCapability.CHAT],
        )

    def _build_completion_body(self, request: LLMRequest) -> dict[str, Any]:
        """Map an ``LLMRequest`` to the OpenRouter chat completions body."""
        body: dict[str, Any] = {
            "model": request.model.model_id,
            "messages": [
                self._message_to_api_dict(message) for message in request.messages
            ],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        return body

    @staticmethod
    def _message_to_api_dict(message: Message) -> dict[str, str]:
        """Convert a conversation message to the OpenAI message format."""
        return {"role": message.role.value, "content": message.content}

    def _parse_completion_response(
        self,
        payload: dict[str, Any],
        requested_model: ModelInfo,
    ) -> LLMResponse:
        """Parse an OpenRouter chat completion response."""
        choices = payload.get("choices", [])
        if not choices:
            raise LLMCompletionError("OpenRouter returned no completion choices")

        first_choice = choices[0]
        message = first_choice.get("message", {})
        content = message.get("content", "")
        finish_reason = first_choice.get("finish_reason")
        usage = payload.get("usage", {})
        model_id = payload.get("model", requested_model.model_id)

        logger.info(
            "OpenRouter completion success | model=%s finish_reason=%s",
            model_id,
            finish_reason,
        )

        return LLMResponse(
            content=content,
            model=ModelInfo(
                provider=LLMProviderName.OPENROUTER,
                model_id=model_id,
                display_name=model_id,
                capabilities=requested_model.capabilities,
            ),
            finish_reason=finish_reason,
            usage={
                key: int(value)
                for key, value in usage.items()
                if isinstance(value, int)
            },
            metadata={"provider_response_id": payload.get("id")},
        )

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        """Extract a human-readable error message from an HTTP error response."""
        try:
            payload = response.json()
        except ValueError:
            return response.text or f"HTTP {response.status_code}"

        error = payload.get("error")
        if isinstance(error, dict):
            return str(error.get("message", error))
        if isinstance(error, str):
            return error
        return response.text or f"HTTP {response.status_code}"
