"""Tests for the tool registry."""

from typing import Any

import pytest
from pydantic import BaseModel

from app.tool_calling.registry import (
    ToolAlreadyRegisteredError,
    ToolDefinition,
    ToolNotFoundError,
    ToolRegistry,
)


class Input(BaseModel):
    value: int


async def handler(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    return {"value": arguments["value"]}


def definition() -> ToolDefinition:
    return ToolDefinition(
        name="sample_tool",
        description="Sample test tool.",
        args_schema=Input,
        handler=handler,
    )


def test_registers_tool() -> None:
    registry = ToolRegistry()

    registry.register(definition())

    assert registry.contains("sample_tool")


def test_duplicate_tool_rejected() -> None:
    registry = ToolRegistry()

    registry.register(definition())

    with pytest.raises(ToolAlreadyRegisteredError):
        registry.register(definition())


def test_unknown_tool_rejected() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError):
        registry.get("missing_tool")
