"""Tool registry tests."""

from __future__ import annotations

import pytest

from app.tools import build_tool_platform
from app.tools.exceptions import ToolNotFoundError, ToolRegistrationError
from app.tools.schemas.enums import ToolCategory
from tests.tools.stub_tool import StubEchoTool


@pytest.fixture
def platform():
    """Fresh tool platform for each test."""
    return build_tool_platform()


def test_register_and_find_tool(platform) -> None:
    """Registry registers and finds tools."""
    tool = StubEchoTool()
    definition = platform.registry.register(tool)
    assert definition.id == "test.echo"
    assert platform.registry.find("test.echo") is tool


def test_unregister_tool(platform) -> None:
    """Registry unregisters tools."""
    platform.registry.register(StubEchoTool())
    removed = platform.registry.unregister("test.echo")
    assert removed.id == "test.echo"
    with pytest.raises(ToolNotFoundError):
        platform.registry.find("test.echo")


def test_duplicate_registration_raises(platform) -> None:
    """Duplicate tool IDs raise registration error."""
    platform.registry.register(StubEchoTool())
    with pytest.raises(ToolRegistrationError):
        platform.registry.register(StubEchoTool())


def test_search_tools(platform) -> None:
    """Search finds tools by description."""
    platform.registry.register(StubEchoTool())
    results = platform.registry.search("echo")
    assert len(results) == 1
    assert results[0].id == "test.echo"


def test_group_by_category(platform) -> None:
    """Tools group by category."""
    platform.registry.register(StubEchoTool())
    groups = platform.registry.group_by_category()
    assert ToolCategory.SYSTEM in groups
    assert len(groups[ToolCategory.SYSTEM]) == 1
