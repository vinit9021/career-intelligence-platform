"""Cross-module tests for memory and tool security."""

from __future__ import annotations

import pytest

from app.memory.manager import MemoryManager
from app.memory.store import InMemoryMemoryStore
from app.tool_calling.models import ToolCallRequest
from app.tool_calling.runtime import build_default_tool_runtime


@pytest.mark.asyncio
async def test_long_term_memory_is_user_isolated() -> None:
    """One user's persistent memory cannot leak to another."""

    memory = MemoryManager(InMemoryMemoryStore())

    await memory.remember(
        user_id="user-a",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
        value="AI Engineer",
    )

    user_a = await memory.recall(
        user_id="user-a",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
    )

    user_b = await memory.recall(
        user_id="user-b",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
    )

    assert user_a == "AI Engineer"

    assert user_b is None


@pytest.mark.asyncio
async def test_short_term_memory_is_session_isolated() -> None:
    """Workflow memory cannot leak between sessions."""

    memory = MemoryManager(InMemoryMemoryStore())

    await memory.remember(
        user_id="user-a",
        scope="short_term",
        namespace="workflow",
        key="current_job",
        value="Backend Engineer",
        session_id="session-a",
    )

    same_session = await memory.recall(
        user_id="user-a",
        scope="short_term",
        namespace="workflow",
        key="current_job",
        session_id="session-a",
    )

    other_session = await memory.recall(
        user_id="user-a",
        scope="short_term",
        namespace="workflow",
        key="current_job",
        session_id="session-b",
    )

    assert same_session == "Backend Engineer"

    assert other_session is None


@pytest.mark.asyncio
async def test_tool_permissions_are_enforced() -> None:
    """An agent cannot call tools outside its allowlist."""

    runtime = build_default_tool_runtime()

    denied = await runtime.call(
        agent_name="cover_letter",
        request=ToolCallRequest(
            tool_name="keyword_overlap",
            arguments={
                "resume_keywords": ["Python"],
                "job_keywords": ["Python"],
            },
        ),
    )

    assert denied.status == "denied"

    assert denied.succeeded is False


@pytest.mark.asyncio
async def test_allowed_agent_tool_executes() -> None:
    """Allowed tool calls return structured results."""

    runtime = build_default_tool_runtime()

    result = await runtime.call(
        agent_name="resume_matching",
        request=ToolCallRequest(
            tool_name="keyword_overlap",
            arguments={
                "resume_keywords": [
                    "Python",
                    "FastAPI",
                ],
                "job_keywords": [
                    "Python",
                    "Docker",
                ],
            },
        ),
    )

    assert result.status == "success"

    assert result.succeeded is True

    assert result.output["matched_keywords"] == ["python"]

    assert result.output["missing_keywords"] == ["docker"]


@pytest.mark.asyncio
async def test_unknown_tool_fails_safely() -> None:
    """Unknown tool names never execute arbitrary behavior."""

    runtime = build_default_tool_runtime()

    result = await runtime.call(
        agent_name="resume_matching",
        request=ToolCallRequest(
            tool_name="unknown_tool",
            arguments={},
        ),
    )

    assert result.status == "invalid"

    assert result.error is not None
