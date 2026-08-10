"""Coverage for remaining framework edge paths."""

from __future__ import annotations

from types import ModuleType
from typing import Any

import pytest
from pydantic import BaseModel

from app.memory.manager import (
    MemoryManager,
)
from app.memory.models import (
    MemoryRecord,
)
from app.memory.policy import (
    MemoryPolicy,
    MemoryPolicyError,
)
from app.memory.store import (
    InMemoryMemoryStore,
)
from app.prompts.management.catalog import (
    _find_prompt_constant,
)
from app.prompts.management.manager import (
    PromptManager,
    build_chat_prompt,
)
from app.prompts.management.models import (
    PromptDefinition,
)
from app.prompts.management.registry import (
    PromptNotFoundError,
    PromptRegistry,
)
from app.tool_calling.audit import (
    NullToolAuditSink,
)
from app.tool_calling.models import (
    ToolCallRequest,
    ToolCallResult,
)
from app.tool_calling.registry import (
    ToolDefinition,
    ToolRegistry,
)
from app.tool_calling.runtime import (
    build_default_tool_runtime,
)
from app.workflow_execution.history import (
    InMemoryWorkflowHistory,
)


def prompt(
    version: str,
    *,
    system: str = "Use {context}",
) -> PromptDefinition:
    return PromptDefinition(
        name="coverage_prompt",
        agent_name="Coverage Agent",
        version=version,
        system_prompt=system,
        user_prompt="Input {message}",
    )


def test_prompt_registry_extra_paths() -> None:
    registry = PromptRegistry()

    registry.register(prompt("1.0.0"))

    registry.register(
        prompt(
            "2.0.0",
            system="New {context}",
        )
    )

    assert registry.versions("coverage_prompt") == [
        "2.0.0",
        "1.0.0",
    ]

    assert registry.names() == ["coverage_prompt"]

    assert registry.latest_prompts()[0].version == "2.0.0"

    replacement = prompt(
        "2.0.0",
        system="Replacement {context}",
    )

    registry.register(
        replacement,
        replace=True,
    )

    assert registry.get("coverage_prompt").system_prompt == "Replacement {context}"

    with pytest.raises(PromptNotFoundError):
        registry.versions("missing")


def test_prompt_manager_variable_validation() -> None:
    registry = PromptRegistry()

    registry.register(prompt("1.0.0"))

    manager = PromptManager(registry)

    assert manager.validate_variables(
        "coverage_prompt",
        {"context": "value"},
    ) == ["message"]


def test_default_chat_prompt_helper() -> None:
    result = build_chat_prompt("resume_parser")

    assert result.messages


def test_prompt_constant_errors() -> None:
    missing = ModuleType("missing_prompts")

    with pytest.raises(
        ValueError,
        match="No prompt constant",
    ):
        _find_prompt_constant(
            missing,
            "SYSTEM_PROMPT",
        )

    duplicate = ModuleType("duplicate_prompts")

    vars(duplicate)["FIRST_SYSTEM_PROMPT"] = "first"

    vars(duplicate)["SECOND_SYSTEM_PROMPT"] = "second"

    with pytest.raises(
        ValueError,
        match="Multiple prompt constants",
    ):
        _find_prompt_constant(
            duplicate,
            "SYSTEM_PROMPT",
        )


def test_memory_policy_size_validation() -> None:
    with pytest.raises(ValueError):
        MemoryPolicy(max_value_bytes=0)

    record = MemoryRecord(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="large",
        value=("x" * 100),
    )

    with pytest.raises(
        MemoryPolicyError,
        match="maximum size",
    ):
        MemoryPolicy(max_value_bytes=10).validate(record)


@pytest.mark.asyncio
async def test_memory_namespace_and_clear() -> None:
    manager = MemoryManager(InMemoryMemoryStore())

    await manager.remember(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="role",
        value="AI Engineer",
    )

    namespace = await manager.recall_namespace(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
    )

    assert namespace == {"role": "AI Engineer"}

    await manager.remember(
        user_id="u1",
        scope="short_term",
        namespace="workflow",
        key="step",
        value=1,
        session_id="s1",
    )

    assert (
        await manager.clear_session(
            user_id="u1",
            session_id="s1",
        )
        == 1
    )


class ToolInput(BaseModel):
    value: int


async def tool_handler(
    arguments: dict[str, Any],
) -> dict[str, Any]:
    return {"value": arguments["value"]}


def test_tool_definition_validation() -> None:
    with pytest.raises(ValueError):
        ToolDefinition(
            name="",
            description="description",
            args_schema=ToolInput,
            handler=tool_handler,
        )

    with pytest.raises(ValueError):
        ToolDefinition(
            name="tool",
            description="",
            args_schema=ToolInput,
            handler=tool_handler,
        )

    with pytest.raises(ValueError):
        ToolDefinition(
            name="tool",
            description="description",
            args_schema=ToolInput,
            handler=tool_handler,
            timeout_seconds=0,
        )


def test_tool_registry_replace_and_definitions() -> None:
    registry = ToolRegistry()

    first = ToolDefinition(
        name="sample_tool",
        description="First",
        args_schema=ToolInput,
        handler=tool_handler,
    )

    second = ToolDefinition(
        name="sample_tool",
        description="Second",
        args_schema=ToolInput,
        handler=tool_handler,
    )

    registry.register(first)

    registry.register(
        second,
        replace=True,
    )

    assert registry.names() == ["sample_tool"]

    assert registry.definitions()[0].description == "Second"


def test_tool_result_succeeded_property() -> None:
    success = ToolCallResult(
        call_id="1",
        tool_name="tool",
        agent_name="agent",
        status="success",
        duration_ms=1,
    )

    failure = ToolCallResult(
        call_id="2",
        tool_name="tool",
        agent_name="agent",
        status="failed",
        duration_ms=1,
    )

    assert success.succeeded is True

    assert failure.succeeded is False


@pytest.mark.asyncio
async def test_null_audit_sink() -> None:
    sink = NullToolAuditSink()

    await sink.write(
        ToolCallResult(
            call_id="1",
            tool_name="tool",
            agent_name="agent",
            status="success",
            duration_ms=0,
        )
    )


@pytest.mark.asyncio
async def test_tool_runtime_call_and_langchain_adapter() -> None:
    runtime = build_default_tool_runtime()

    result = await runtime.call(
        agent_name="resume_matching",
        request=ToolCallRequest(
            tool_name="keyword_overlap",
            arguments={
                "resume_keywords": ["Python"],
                "job_keywords": ["Python"],
            },
        ),
    )

    assert result.succeeded is True

    tools = runtime.tools_for_agent("resume_matching")

    evidence_tool = next(tool for tool in tools if tool.name == "evidence_lookup")

    output = await evidence_tool.ainvoke(
        {
            "text": ("Built services using Python."),
            "query": "Python",
            "context_chars": 10,
        }
    )

    assert output["status"] == "success"


@pytest.mark.asyncio
async def test_history_missing_and_zero_limit() -> None:
    history = InMemoryWorkflowHistory()

    assert await history.get("missing") is None

    assert (
        list(
            await history.list_for_user(
                "u1",
                limit=0,
            )
        )
        == []
    )
