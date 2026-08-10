"""Audit interfaces for agent tool executions."""

from __future__ import annotations

from typing import Protocol

from app.tool_calling.models import (
    ToolCallResult,
)


class ToolAuditSink(Protocol):
    """Receives completed tool-call records."""

    async def write(
        self,
        result: ToolCallResult,
    ) -> None:
        """Persist one tool-call audit event."""
        ...


class NullToolAuditSink:
    """Default audit sink when persistence is disabled."""

    async def write(
        self,
        result: ToolCallResult,
    ) -> None:
        del result


class InMemoryToolAuditSink:
    """Audit sink used for development and tests."""

    def __init__(self) -> None:
        self._events: list[ToolCallResult] = []

    async def write(
        self,
        result: ToolCallResult,
    ) -> None:
        self._events.append(result.model_copy(deep=True))

    def events(
        self,
    ) -> list[ToolCallResult]:
        """Return recorded events."""

        return [event.model_copy(deep=True) for event in self._events]
