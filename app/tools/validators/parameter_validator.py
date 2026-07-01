"""Tool parameter validation."""

from __future__ import annotations

from typing import Any

from app.tools.exceptions import ToolValidationError
from app.tools.schemas.parameters import ToolParameter


class ParameterValidator:
    """Validates tool input parameters against declared schemas."""

    def validate(
        self,
        tool_id: str,
        parameters: dict[str, Any],
        schema: list[ToolParameter],
    ) -> dict[str, Any]:
        """Validate and normalize parameters.

        Args:
            tool_id: Tool identifier for error messages.
            parameters: Raw input parameters.
            schema: Declared parameter schema.

        Returns:
            Validated parameters with defaults applied.

        Raises:
            ToolValidationError: If validation fails.
        """
        validated: dict[str, Any] = dict(parameters)
        schema_by_name = {p.name: p for p in schema}

        for param in schema:
            if param.required and param.name not in validated:
                msg = f"Missing required parameter: {param.name}"
                raise ToolValidationError(msg, tool_id=tool_id)

        for name, value in list(validated.items()):
            if name not in schema_by_name:
                msg = f"Unknown parameter: {name}"
                raise ToolValidationError(msg, tool_id=tool_id)

            param = schema_by_name[name]
            self._validate_type(tool_id, name, value, param)
            if param.enum is not None and value not in param.enum:
                msg = f"Parameter '{name}' must be one of {param.enum}"
                raise ToolValidationError(msg, tool_id=tool_id)

        for param in schema:
            if param.name not in validated and param.default is not None:
                validated[param.name] = param.default

        return validated

    def _validate_type(
        self,
        tool_id: str,
        name: str,
        value: Any,
        param: ToolParameter,
    ) -> None:
        """Validate a single parameter type.

        Args:
            tool_id: Tool identifier.
            name: Parameter name.
            value: Parameter value.
            param: Parameter schema.

        Raises:
            ToolValidationError: If type does not match.
        """
        type_map: dict[str, type[Any] | tuple[type[Any], ...]] = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        expected = type_map.get(param.type)
        if expected is None:
            return
        if isinstance(expected, tuple):
            if not isinstance(value, expected):
                self._raise_type_error(tool_id, name, param.type, value)
            return
        if not isinstance(value, expected):
            self._raise_type_error(tool_id, name, param.type, value)

    def _raise_type_error(
        self,
        tool_id: str,
        name: str,
        expected_type: str,
        value: Any,
    ) -> None:
        """Raise a validation error for type mismatch."""
        msg = (
            f"Parameter '{name}' expected type '{expected_type}', "
            f"got '{type(value).__name__}'"
        )
        raise ToolValidationError(msg, tool_id=tool_id)
