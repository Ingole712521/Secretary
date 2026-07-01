"""Tool executor tests."""

from __future__ import annotations

import pytest

from app.tools import build_tool_platform
from app.tools.exceptions import (
    ToolPermissionDeniedError,
    ToolSecurityError,
    ToolValidationError,
)
from app.tools.schemas.enums import ToolPermissionLevel
from app.tools.schemas.requests import ToolExecutionRequest
from app.tools.security.policies import ToolSecurityPolicy
from tests.tools.stub_tool import StubEchoTool


@pytest.fixture
def platform():
    """Tool platform with stub tool registered."""
    platform = build_tool_platform()
    platform.registry.register(StubEchoTool())
    return platform


@pytest.mark.asyncio
async def test_execute_tool_success(platform) -> None:
    """Executor runs tool and returns structured response."""
    request = ToolExecutionRequest(
        tool_id="test.echo",
        parameters={"message": "hello"},
        caller_permissions=[
            ToolPermissionLevel.READ,
            ToolPermissionLevel.EXECUTE,
        ],
        correlation_id="test-corr-1",
    )
    response = await platform.executor.execute(request)
    assert response.validated is True
    assert response.permission_granted is True
    assert response.result.is_success
    assert response.result.output["echo"] == "hello"
    assert response.duration_ms >= 0
    assert len(response.logs) > 0


@pytest.mark.asyncio
async def test_dry_run_skips_execute(platform) -> None:
    """Dry run uses tool.dry_run instead of execute."""
    request = ToolExecutionRequest(
        tool_id="test.echo",
        parameters={"message": "hello"},
        caller_permissions=[ToolPermissionLevel.READ, ToolPermissionLevel.EXECUTE],
        dry_run=True,
    )
    response = await platform.executor.execute(request)
    assert response.result.output.get("dry_run") is True


@pytest.mark.asyncio
async def test_missing_permission_raises(platform) -> None:
    """Executor rejects callers without required permissions."""
    request = ToolExecutionRequest(
        tool_id="test.echo",
        parameters={"message": "hello"},
        caller_permissions=[ToolPermissionLevel.READ],
    )
    with pytest.raises(ToolPermissionDeniedError):
        await platform.executor.execute(request)


@pytest.mark.asyncio
async def test_invalid_parameter_raises(platform) -> None:
    """Executor rejects missing required parameters."""
    request = ToolExecutionRequest(
        tool_id="test.echo",
        parameters={},
        caller_permissions=[ToolPermissionLevel.READ, ToolPermissionLevel.EXECUTE],
    )
    with pytest.raises(ToolValidationError):
        await platform.executor.execute(request)


@pytest.mark.asyncio
async def test_blacklist_blocks_tool() -> None:
    """Security policy blacklist blocks tool execution."""
    policy = ToolSecurityPolicy(blacklist=["test.echo"])
    platform = build_tool_platform(policy=policy)
    platform.registry.register(StubEchoTool())
    request = ToolExecutionRequest(
        tool_id="test.echo",
        parameters={"message": "hi"},
        caller_permissions=[ToolPermissionLevel.READ, ToolPermissionLevel.EXECUTE],
    )
    with pytest.raises(ToolSecurityError):
        await platform.executor.execute(request)


@pytest.mark.asyncio
async def test_audit_log_captures_execution(platform) -> None:
    """Executor stores audit log entries."""
    request = ToolExecutionRequest(
        tool_id="test.echo",
        parameters={"message": "audit"},
        caller_permissions=[ToolPermissionLevel.READ, ToolPermissionLevel.EXECUTE],
    )
    await platform.executor.execute(request)
    log = platform.executor.get_audit_log()
    assert len(log) == 1
    assert log[0].tool_id == "test.echo"
