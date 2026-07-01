"""Convert tool platform definitions to LLM function-calling format."""

from __future__ import annotations

from typing import Any

from app.tools.registry.registry import ToolRegistry
from app.tools.schemas.parameters import ToolDefinition, ToolParameter


def tool_id_to_function_name(tool_id: str) -> str:
    """Map a tool ID to an OpenAI-compatible function name.

    Args:
        tool_id: Registry tool identifier (e.g. ``terminal.run``).

    Returns:
        Function name safe for provider APIs (e.g. ``terminal_run``).
    """
    return tool_id.replace(".", "_")


def function_name_to_tool_id(function_name: str, registry: ToolRegistry) -> str:
    """Resolve a provider function name back to a registry tool ID.

    Args:
        function_name: Function name from an LLM tool call.
        registry: Tool registry for lookup.

    Returns:
        Matching tool identifier.

    Raises:
        ToolNotFoundError: When no registered tool matches the function name.
    """
    from app.tools.exceptions import ToolNotFoundError

    for definition in registry.list_tools():
        if tool_id_to_function_name(definition.id) == function_name:
            return definition.id
        if definition.id == function_name:
            return definition.id

    raise ToolNotFoundError(function_name)


def parameters_to_json_schema(parameters: list[ToolParameter]) -> dict[str, Any]:
    """Convert tool parameters to a JSON Schema object.

    Args:
        parameters: Declared tool parameters.

    Returns:
        JSON Schema ``object`` for OpenAI function calling.
    """
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in parameters:
        schema: dict[str, Any] = {
            "type": param.type,
            "description": param.description,
        }
        if param.enum is not None:
            schema["enum"] = param.enum
        if param.default is not None:
            schema["default"] = param.default
        properties[param.name] = schema
        if param.required:
            required.append(param.name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def definition_to_openai_tool(definition: ToolDefinition) -> dict[str, Any]:
    """Convert a tool definition to an OpenAI-compatible tool entry.

    Args:
        definition: Registered tool metadata.

    Returns:
        Tool dictionary for chat completion requests.
    """
    return {
        "type": "function",
        "function": {
            "name": tool_id_to_function_name(definition.id),
            "description": definition.description,
            "parameters": parameters_to_json_schema(definition.parameters),
        },
    }


def registry_to_openai_tools(registry: ToolRegistry) -> list[dict[str, Any]]:
    """Export all registered tools in OpenAI function-calling format.

    Args:
        registry: Tool registry.

    Returns:
        List of tool definitions for LLM requests.
    """
    return [
        definition_to_openai_tool(definition)
        for definition in registry.list_tools()
    ]
