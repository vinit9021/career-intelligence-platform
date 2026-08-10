"""Tests for in-memory storage backend."""

import pytest

from app.memory.models import (
    MemoryRecord,
)
from app.memory.store import (
    InMemoryMemoryStore,
)


@pytest.mark.asyncio
async def test_store_saves_and_reads() -> None:
    store = InMemoryMemoryStore()

    record = MemoryRecord(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
        value="AI Engineer",
    )

    await store.upsert(record)

    result = await store.get(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
    )

    assert result is not None

    assert result.value == "AI Engineer"


@pytest.mark.asyncio
async def test_upsert_preserves_id() -> None:
    store = InMemoryMemoryStore()

    first = await store.upsert(
        MemoryRecord(
            user_id="u1",
            scope="long_term",
            namespace="career_goals",
            key="target_role",
            value="Backend Engineer",
        )
    )

    second = await store.upsert(
        MemoryRecord(
            user_id="u1",
            scope="long_term",
            namespace="career_goals",
            key="target_role",
            value="AI Engineer",
        )
    )

    assert first.id == second.id

    assert second.value == "AI Engineer"


@pytest.mark.asyncio
async def test_sessions_are_isolated() -> None:
    store = InMemoryMemoryStore()

    await store.upsert(
        MemoryRecord(
            user_id="u1",
            scope="short_term",
            namespace="workflow",
            key="step",
            value=1,
            session_id="s1",
        )
    )

    result = await store.get(
        user_id="u1",
        scope="short_term",
        namespace="workflow",
        key="step",
        session_id="s2",
    )

    assert result is None


@pytest.mark.asyncio
async def test_clear_session() -> None:
    store = InMemoryMemoryStore()

    await store.upsert(
        MemoryRecord(
            user_id="u1",
            scope="short_term",
            namespace="workflow",
            key="step",
            value=1,
            session_id="s1",
        )
    )

    deleted = await store.clear_session(
        user_id="u1",
        session_id="s1",
    )

    assert deleted == 1
