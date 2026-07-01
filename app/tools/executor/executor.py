"""Tool execution engine."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from app.constants import LOGGER_ROOT
from app.tools.exceptions import ToolExecutionError, ToolNotFoundError
from app.tools.registry.registry import ToolRegistry
from app.tools.schemas.requests import ToolExecutionRequest
from app.tools.schemas.responses import ToolExecutionResponse
from app.tools.validators.tool_validator import ToolValidator

if TYPE_CHECKING:
    from app.tools.security.policies import Sandbox

logger = logging.getLogger(f"{LOGGER_ROOT}.tools.executor")


class ToolExecutor:
    """Executes registered tools with validation, permissions, and auditing.

    The executor never bypasses validation or security checks. All
    executions produce structured ``ToolExecutionResponse`` objects
    with timing and log metadata.

    Attributes:
        _registry: Tool registry for lookup.
        _validator: Composite validation pipeline.
        _sandbox: Optional sandbox for isolated execution.
        _audit_log: In-memory execution audit entries (Sprint 3).
    """

    def __init__(
        self,
        registry: ToolRegistry,
        validator: ToolValidator,
        sandbox: Sandbox | None = None,
    ) -> None:
        """Initialize the executor.

        Args:
            registry: Tool registry.
            validator: Validation pipeline.
            sandbox: Optional sandbox port (interface only in Sprint 3).
        """
        self._registry = registry
        self._validator = validator
        self._sandbox = sandbox
        self._audit_log: list[ToolExecutionResponse] = []

    async def execute(self, request: ToolExecutionRequest) -> ToolExecutionResponse:
        """Execute a tool request through the full pipeline.

        Pipeline:
            1. Find tool in registry
            2. Validate parameters, permissions, security
            3. Dry-run or execute based on request flag
            4. Capture result, logs, and duration
            5. Return structured response

        Args:
            request: Tool execution request.

        Returns:
            Structured execution response.

        Raises:
            ToolNotFoundError: If tool is not registered.
            ToolValidationError: On validation failure.
            ToolPermissionDeniedError: On permission failure.
            ToolSecurityError: On security policy violation.
        """
        start = time.perf_counter()
        logs: list[str] = []
        logs.append(f"execution started: tool={request.tool_id}")

        try:
            tool = self._registry.find(request.tool_id)
        except ToolNotFoundError:
            logs.append(f"tool not found: {request.tool_id}")
            raise

        confirmed = bool(request.metadata.get("confirmed", False))
        validated_params, grant = self._validator.validate_execution(
            tool,
            request.parameters,
            request.caller_permissions,
            confirmed=confirmed,
        )
        logs.append("validation passed")

        if self._sandbox is not None:
            await self._sandbox.prepare(tool.id)
            logs.append("sandbox prepared")

        try:
            if request.dry_run:
                result = await tool.dry_run(validated_params)
                logs.append("dry run completed")
            else:
                tool_validate_result = await tool.validate(validated_params)
                if tool_validate_result.is_failure:
                    msg = tool_validate_result.error or "Tool self-validation failed"
                    raise ToolExecutionError(msg, tool_id=tool.id)
                result = await tool.execute(validated_params)
                logs.append(f"execution completed: status={result.status.value}")
        finally:
            if self._sandbox is not None:
                await self._sandbox.cleanup(tool.id)
                logs.append("sandbox cleaned up")

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response = ToolExecutionResponse(
            tool_id=tool.id,
            result=result,
            duration_ms=duration_ms,
            logs=logs,
            correlation_id=request.correlation_id,
            validated=True,
            permission_granted=True,
            metadata={
                "caller_permissions": [p.value for p in grant.levels],
                "dry_run": request.dry_run,
            },
        )

        self._audit_log.append(response)
        logger.info(
            "tool executed",
            extra={
                "tool_id": tool.id,
                "duration_ms": duration_ms,
                "status": result.status.value,
                "correlation_id": request.correlation_id,
            },
        )
        return response

    def get_audit_log(self) -> list[ToolExecutionResponse]:
        """Return captured execution audit entries.

        Returns:
            Copy of the in-memory audit log.
        """
        return list(self._audit_log)

    async def health_check(self, tool_id: str) -> bool:
        """Check health of a registered tool.

        Args:
            tool_id: Tool identifier.

        Returns:
            True if the tool reports healthy.

        Raises:
            ToolNotFoundError: If tool is not registered.
        """
        tool = self._registry.find(tool_id)
        return await tool.health()
