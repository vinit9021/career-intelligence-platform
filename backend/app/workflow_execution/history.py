"""Workflow execution history abstraction."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.workflow_execution.models import (
    WorkflowExecutionRecord,
)


class WorkflowHistory(Protocol):
    """Storage interface for workflow history."""

    async def save(
        self,
        record: WorkflowExecutionRecord,
    ) -> WorkflowExecutionRecord:
        """Create or update one execution record."""
        ...

    async def get(
        self,
        execution_id: str,
    ) -> WorkflowExecutionRecord | None:
        """Return one execution record."""
        ...

    async def list_for_user(
        self,
        user_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[WorkflowExecutionRecord]:
        """Return recent executions for a user."""
        ...


class InMemoryWorkflowHistory:
    """Development/test implementation of workflow history."""

    def __init__(self) -> None:
        self._records: dict[
            str,
            WorkflowExecutionRecord,
        ] = {}

    async def save(
        self,
        record: WorkflowExecutionRecord,
    ) -> WorkflowExecutionRecord:
        stored = record.model_copy(deep=True)

        self._records[stored.execution_id] = stored

        return stored.model_copy(deep=True)

    async def get(
        self,
        execution_id: str,
    ) -> WorkflowExecutionRecord | None:
        record = self._records.get(execution_id)

        if record is None:
            return None

        return record.model_copy(deep=True)

    async def list_for_user(
        self,
        user_id: str,
        *,
        limit: int = 20,
    ) -> Sequence[WorkflowExecutionRecord]:
        if limit <= 0:
            return []

        records = [record for record in self._records.values() if record.user_id == user_id]

        records.sort(
            key=lambda item: item.started_at,
            reverse=True,
        )

        return [record.model_copy(deep=True) for record in records[:limit]]
