"""Tests for safe tool execution."""

import asyncio
from typing import Any

import pytest
from pydantic import BaseModel

from app.tool_calling.audit import (
    InMemoryToolAuditSink,
)
from app.tool_calling.executor import (
    ToolExecutor,
)
from app.tool_calling.models import (
    ToolCallRequest,
)
from app.tool_calling.permissions import (
    ToolPermissionPolicy,
)
from app.tool_calling.registry import (
    ToolDefinition,
    ToolRegistry,
)


class AddInput(BaseModel):
    a: int
    b: int


async def add_handler(
    arguments: dict[str, Any],
) -> dict[str, int]:
    return {"result": (int(arguments["a"]) + int(arguments["b"]))}


def build_executor(
    *,
    allowed: bool = True,
    audit: (InMemoryToolAuditSink | None) = None,
) -> ToolExecutor:
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="add_numbers",
            description="Add two integers.",
            args_schema=AddInput,
            handler=add_handler,
        )
    )

    permissions = ToolPermissionPolicy({"test_agent": ({"add_numbers"} if allowed else set())})

    return ToolExecutor(
        registry=registry,
        permissions=permissions,
        audit_sink=audit,
    )


@pytest.mark.asyncio
async def test_successful_tool_call() -> None:
    executor = build_executor()

    result = await executor.execute(
        agent_name="test_agent",
        request=ToolCallRequest(
            tool_name="add_numbers",
            arguments={
                "a": 2,
                "b": 3,
            },
        ),
    )

    assert result.status == "success"

    assert result.output == {"result": 5}


@pytest.mark.asyncio
async def test_invalid_arguments() -> None:
    executor = build_executor()

    result = await executor.execute(
        agent_name="test_agent",
        request=ToolCallRequest(
            tool_name="add_numbers",
            arguments={
                "a": "wrong",
                "b": 3,
            },
        ),
    )

    assert result.status == "invalid"

    assert result.error is not None


@pytest.mark.asyncio
async def test_permission_denied() -> None:
    executor = build_executor(allowed=False)

    result = await executor.execute(
        agent_name="test_agent",
        request=ToolCallRequest(
            tool_name="add_numbers",
            arguments={
                "a": 2,
                "b": 3,
            },
        ),
    )

    assert result.status == "denied"


@pytest.mark.asyncio
async def test_unknown_tool() -> None:
    executor = build_executor()

    result = await executor.execute(
        agent_name="test_agent",
        request=ToolCallRequest(
            tool_name="unknown_tool",
        ),
    )

    assert result.status == "invalid"


@pytest.mark.asyncio
async def test_tool_failure() -> None:
    class Input(BaseModel):
        value: str

    async def failing(
        arguments: dict[str, Any],
    ) -> Any:
        del arguments

        raise RuntimeError("tool failed")

    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="failing_tool",
            description="Always fails.",
            args_schema=Input,
            handler=failing,
        )
    )

    executor = ToolExecutor(
        registry=registry,
        permissions=(ToolPermissionPolicy({"agent": {"failing_tool"}})),
    )

    result = await executor.execute(
        agent_name="agent",
        request=ToolCallRequest(
            tool_name="failing_tool",
            arguments={"value": "x"},
        ),
    )

    assert result.status == "failed"

    assert result.error == "tool failed"


@pytest.mark.asyncio
async def test_tool_timeout() -> None:
    class Input(BaseModel):
        value: str

    async def slow(
        arguments: dict[str, Any],
    ) -> dict[str, str]:
        del arguments

        await asyncio.sleep(0.05)

        return {"status": "done"}

    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="slow_tool",
            description="Slow tool.",
            args_schema=Input,
            handler=slow,
            timeout_seconds=0.001,
        )
    )

    executor = ToolExecutor(
        registry=registry,
        permissions=(ToolPermissionPolicy({"agent": {"slow_tool"}})),
    )

    result = await executor.execute(
        agent_name="agent",
        request=ToolCallRequest(
            tool_name="slow_tool",
            arguments={"value": "x"},
        ),
    )

    assert result.status == "timeout"


@pytest.mark.asyncio
async def test_tool_call_is_audited() -> None:
    audit = InMemoryToolAuditSink()

    executor = build_executor(audit=audit)

    await executor.execute(
        agent_name="test_agent",
        request=ToolCallRequest(
            tool_name="add_numbers",
            arguments={
                "a": 1,
                "b": 2,
            },
        ),
    )

    events = audit.events()

    assert len(events) == 1

    assert events[0].tool_name == "add_numbers"

    assert events[0].status == "success"
