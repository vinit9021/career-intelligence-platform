"""Tests for workflow execution history."""

import pytest

from app.workflow_execution.history import (
    InMemoryWorkflowHistory,
)
from app.workflow_execution.models import (
    WorkflowExecutionRecord,
)


@pytest.mark.asyncio
async def test_history_saves_record() -> None:
    history = InMemoryWorkflowHistory()

    record = WorkflowExecutionRecord(
        execution_id="e1",
        user_id="u1",
        session_id="s1",
        status="completed",
        enabled_nodes=["resume_parser"],
    )

    await history.save(record)

    saved = await history.get("e1")

    assert saved is not None
    assert saved.status == "completed"


@pytest.mark.asyncio
async def test_history_updates_same_execution() -> None:
    history = InMemoryWorkflowHistory()

    await history.save(
        WorkflowExecutionRecord(
            execution_id="e1",
            user_id="u1",
            session_id="s1",
            status="running",
            enabled_nodes=["resume_parser"],
        )
    )

    await history.save(
        WorkflowExecutionRecord(
            execution_id="e1",
            user_id="u1",
            session_id="s1",
            status="completed",
            enabled_nodes=["resume_parser"],
        )
    )

    saved = await history.get("e1")

    assert saved is not None
    assert saved.status == "completed"


@pytest.mark.asyncio
async def test_history_is_user_scoped() -> None:
    history = InMemoryWorkflowHistory()

    for user_id in (
        "u1",
        "u2",
    ):
        await history.save(
            WorkflowExecutionRecord(
                user_id=user_id,
                session_id="s1",
                status="completed",
                enabled_nodes=["resume_parser"],
            )
        )

    records = await history.list_for_user("u1")

    assert len(records) == 1

    assert records[0].user_id == "u1"
