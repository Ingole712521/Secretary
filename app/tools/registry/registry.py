"""Tool registration and discovery."""

from __future__ import annotations

from collections import defaultdict

from app.tools.exceptions import ToolNotFoundError, ToolRegistrationError
from app.tools.interfaces.tool import Tool
from app.tools.schemas.enums import ToolCategory
from app.tools.schemas.parameters import ToolDefinition


class ToolRegistry:
    """Central registry for tool registration and discovery.

    Thread-safe operations are not guaranteed in Sprint 3; a future
    sprint may add locking for concurrent registration.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> ToolDefinition:
        """Register a tool instance.

        Args:
            tool: Tool implementing the ``Tool`` protocol.

        Returns:
            Registered tool definition metadata.

        Raises:
            ToolRegistrationError: If a tool with the same ID exists.
        """
        if tool.id in self._tools:
            msg = f"Tool already registered: {tool.id}"
            raise ToolRegistrationError(msg, tool_id=tool.id)

        self._tools[tool.id] = tool
        return self._to_definition(tool)

    def unregister(self, tool_id: str) -> ToolDefinition:
        """Remove a tool from the registry.

        Args:
            tool_id: Tool identifier to remove.

        Returns:
            Definition of the removed tool.

        Raises:
            ToolNotFoundError: If the tool is not registered.
        """
        tool = self._tools.pop(tool_id, None)
        if tool is None:
            raise ToolNotFoundError(tool_id)
        return self._to_definition(tool)

    def find(self, tool_id: str) -> Tool:
        """Find a tool by ID.

        Args:
            tool_id: Tool identifier.

        Returns:
            Registered tool instance.

        Raises:
            ToolNotFoundError: If not found.
        """
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ToolNotFoundError(tool_id)
        return tool

    def get_definition(self, tool_id: str) -> ToolDefinition:
        """Return metadata definition for a tool.

        Args:
            tool_id: Tool identifier.

        Returns:
            Tool definition.

        Raises:
            ToolNotFoundError: If not found.
        """
        return self._to_definition(self.find(tool_id))

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tool definitions.

        Returns:
            All tool definitions sorted by name.
        """
        definitions = [self._to_definition(t) for t in self._tools.values()]
        return sorted(definitions, key=lambda d: d.name)

    def search(self, query: str) -> list[ToolDefinition]:
        """Search tools by name, description, or tags.

        Args:
            query: Case-insensitive search string.

        Returns:
            Matching tool definitions.
        """
        query_lower = query.lower()
        results: list[ToolDefinition] = []
        for tool in self._tools.values():
            definition = self._to_definition(tool)
            haystack = " ".join(
                [
                    definition.name,
                    definition.description,
                    " ".join(definition.tags),
                    definition.category.value,
                ],
            ).lower()
            if query_lower in haystack:
                results.append(definition)
        return sorted(results, key=lambda d: d.name)

    def group_by_category(self) -> dict[ToolCategory, list[ToolDefinition]]:
        """Group registered tools by category.

        Returns:
            Mapping of category to tool definitions.
        """
        groups: dict[ToolCategory, list[ToolDefinition]] = defaultdict(list)
        for tool in self._tools.values():
            definition = self._to_definition(tool)
            groups[definition.category].append(definition)
        for category in groups:
            groups[category].sort(key=lambda d: d.name)
        return dict(groups)

    def count(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)

    @staticmethod
    def _to_definition(tool: Tool) -> ToolDefinition:
        """Convert a tool instance to a definition model.

        Args:
            tool: Tool instance.

        Returns:
            Tool definition schema.
        """
        return ToolDefinition(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            category=tool.category,
            parameters=list(tool.parameters),
            permissions=list(tool.permissions),
        )
