"""Tests for high-level Memory Manager."""

import pytest

from app.memory.manager import (
    MemoryManager,
)
from app.memory.store import (
    InMemoryMemoryStore,
)


@pytest.fixture
def memory() -> MemoryManager:
    return MemoryManager(InMemoryMemoryStore())


@pytest.mark.asyncio
async def test_remember_and_recall(
    memory: MemoryManager,
) -> None:
    await memory.remember(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
        value="Backend Engineer",
    )

    result = await memory.recall(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
    )

    assert result == "Backend Engineer"


@pytest.mark.asyncio
async def test_memory_can_be_updated(
    memory: MemoryManager,
) -> None:
    await memory.remember(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
        value="Backend Engineer",
    )

    await memory.remember(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
        value="AI Engineer",
    )

    result = await memory.recall(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
    )

    assert result == "AI Engineer"


@pytest.mark.asyncio
async def test_missing_memory_returns_none(
    memory: MemoryManager,
) -> None:
    result = await memory.recall(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="missing",
    )

    assert result is None


@pytest.mark.asyncio
async def test_build_context_separates_scopes(
    memory: MemoryManager,
) -> None:
    await memory.remember(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
        value="AI Engineer",
    )

    await memory.remember(
        user_id="u1",
        scope="short_term",
        namespace="workflow",
        key="current_job",
        value="ML Engineer",
        session_id="s1",
    )

    context = await memory.build_context(
        user_id="u1",
        session_id="s1",
    )

    assert context["long_term"]["career_goals"]["target_role"] == "AI Engineer"

    assert context["short_term"]["workflow"]["current_job"] == "ML Engineer"


@pytest.mark.asyncio
async def test_forget_memory(
    memory: MemoryManager,
) -> None:
    await memory.remember(
        user_id="u1",
        scope="long_term",
        namespace="user_preferences",
        key="tone",
        value="concise",
    )

    deleted = await memory.forget(
        user_id="u1",
        scope="long_term",
        namespace="user_preferences",
        key="tone",
    )

    assert deleted is True

    assert (
        await memory.recall(
            user_id="u1",
            scope="long_term",
            namespace="user_preferences",
            key="tone",
        )
        is None
    )
