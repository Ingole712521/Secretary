"""LLM tool-calling execution loop."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from app.brain.interfaces.llm_provider import LLMProvider
from app.brain.schemas.conversation import Message, MessageRole
from app.brain.schemas.llm import LLMRequest, LLMResponse, ModelInfo
from app.brain.schemas.tools import LLMToolCall
from app.constants import LOGGER_CHAT
from app.models.chat import ToolInvocationSummary
from app.tools.exceptions import ToolConfirmationRequiredError, ToolNotFoundError
from app.tools.llm_format import (
    function_name_to_tool_id,
    tool_id_to_function_name,
)
from app.tools.schemas.enums import ToolPermissionLevel
from app.tools.schemas.requests import ToolExecutionRequest

if TYPE_CHECKING:
    from app.tools.executor.executor import ToolExecutor
    from app.tools.registry.registry import ToolRegistry

logger = logging.getLogger(LOGGER_CHAT)

DEFAULT_CALLER_PERMISSIONS = [
    ToolPermissionLevel.READ,
    ToolPermissionLevel.WRITE,
    ToolPermissionLevel.EXECUTE,
]


class ToolLoopService:
    """Runs an LLM completion loop with tool execution.

    Repeatedly calls the provider until the model returns a final text
    response or the iteration limit is reached.

    Attributes:
        _registry: Tool registry for name resolution.
        _executor: Tool execution engine.
        _max_iterations: Maximum tool loop iterations per chat turn.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        executor: ToolExecutor,
        *,
        max_iterations: int = 5,
    ) -> None:
        """Initialize the tool loop service.

        Args:
            registry: Registered tools.
            executor: Tool executor.
            max_iterations: Maximum provider/tool iterations.
        """
        self._registry = registry
        self._executor = executor
        self._max_iterations = max_iterations

    async def complete_with_tools(
        self,
        provider: LLMProvider,
        model_info: ModelInfo,
        messages: list[Message],
        tools: list[dict[str, object]],
        *,
        temperature: float,
        max_tokens: int | None,
        confirmed: bool,
        correlation_id: str | None = None,
    ) -> tuple[LLMResponse, list[ToolInvocationSummary]]:
        """Complete a chat turn with optional tool invocations.

        Args:
            provider: LLM provider adapter.
            model_info: Selected model metadata.
            messages: Conversation messages including system prompt.
            tools: OpenAI-compatible tool definitions.
            temperature: Sampling temperature.
            max_tokens: Optional max tokens to generate.
            confirmed: Whether dangerous tool execution is confirmed.
            correlation_id: Optional request correlation ID.

        Returns:
            Tuple of final LLM response and tool invocation summaries.

        Raises:
            ToolConfirmationRequiredError: When a tool needs user confirmation.
        """
        working_messages = list(messages)
        tool_summaries: list[ToolInvocationSummary] = []
        final_response: LLMResponse | None = None

        for iteration in range(self._max_iterations):
            llm_request = LLMRequest(
                model=model_info,
                messages=working_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice="auto" if tools else "none",
            )
            response = await provider.complete(llm_request)
            final_response = response

            if not response.tool_calls:
                break

            logger.info(
                "Tool loop iteration %d | tool_calls=%d",
                iteration + 1,
                len(response.tool_calls),
            )

            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=response.content,
                tool_calls=response.tool_calls,
            )
            working_messages.append(assistant_message)

            for tool_call in response.tool_calls:
                summary = await self._execute_tool_call(
                    tool_call,
                    confirmed=confirmed,
                    correlation_id=correlation_id,
                )
                tool_summaries.append(summary)

                working_messages.append(
                    Message(
                        role=MessageRole.TOOL,
                        content=json.dumps(summary.output),
                        tool_call_id=tool_call.id,
                    )
                )
        else:
            logger.warning(
                "Tool loop reached max iterations (%d)",
                self._max_iterations,
            )

        if final_response is None:
            msg = "Tool loop did not produce an LLM response"
            raise RuntimeError(msg)

        return final_response, tool_summaries

    async def _execute_tool_call(
        self,
        tool_call: LLMToolCall,
        *,
        confirmed: bool,
        correlation_id: str | None,
    ) -> ToolInvocationSummary:
        """Execute a single LLM-requested tool call.

        Args:
            tool_call: Provider tool call payload.
            confirmed: Whether dangerous execution was confirmed.
            correlation_id: Optional correlation ID.

        Returns:
            Tool invocation summary.

        Raises:
            ToolConfirmationRequiredError: When confirmation is required.
        """
        try:
            tool_id = function_name_to_tool_id(tool_call.name, self._registry)
        except ToolNotFoundError:
            available = [
                tool_id_to_function_name(definition.id)
                for definition in self._registry.list_tools()
            ]
            logger.warning(
                "LLM requested unknown tool | name=%s available=%s",
                tool_call.name,
                available,
            )
            return ToolInvocationSummary(
                tool_id=tool_call.name,
                status="failure",
                output={
                    "error": f"Unknown tool '{tool_call.name}'.",
                    "available_tools": available,
                    "hint": (
                        "Use one of the available tools. To run a program or "
                        "shell command use 'terminal_run'."
                    ),
                },
                error=f"Unknown tool: {tool_call.name}",
                duration_ms=0.0,
                message="Requested tool does not exist",
            )
        request = ToolExecutionRequest(
            tool_id=tool_id,
            parameters=tool_call.arguments,
            correlation_id=correlation_id,
            caller_permissions=DEFAULT_CALLER_PERMISSIONS,
            metadata={"confirmed": confirmed},
        )

        try:
            execution = await self._executor.execute(request)
        except ToolConfirmationRequiredError:
            raise
        except Exception as exc:
            logger.error("Tool execution failed | tool=%s error=%s", tool_id, exc)
            return ToolInvocationSummary(
                tool_id=tool_id,
                status="failure",
                output={},
                error=str(exc),
                duration_ms=0.0,
            )

        return ToolInvocationSummary(
            tool_id=tool_id,
            status=execution.result.status.value,
            output=execution.result.output,
            error=execution.result.error,
            duration_ms=execution.duration_ms,
            message=execution.result.message,
        )
