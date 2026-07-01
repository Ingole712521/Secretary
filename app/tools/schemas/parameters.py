"""Tool parameter and definition schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel


class ToolParameter(BaseModel):
    """Schema for a single tool input parameter.

    Attributes:
        name: Parameter identifier.
        type: JSON Schema type string (string, integer, boolean, object, array).
        description: Human-readable parameter description.
        required: Whether the parameter is mandatory.
        default: Default value when not provided.
        enum: Allowed values, if restricted.
    """

    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Any | None = None
    enum: list[Any] | None = None


class ToolDefinition(BaseModel):
    """Registered tool metadata exposed by the registry.

    Attributes:
        id: Unique tool identifier.
        name: Human-readable tool name.
        description: What the tool does.
        category: Tool category for grouping and search.
        parameters: Declared input parameters.
        permissions: Required permission levels.
        version: Tool implementation version.
        tags: Optional search tags.
        metadata: Additional tool metadata.
    """

    id: str
    name: str
    description: str
    category: ToolCategory
    parameters: list[ToolParameter] = Field(default_factory=list)
    permissions: list[ToolPermissionLevel] = Field(default_factory=list)
    version: str = "1.0.0"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
