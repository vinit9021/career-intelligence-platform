"""Tests for Agent Registry."""

import pytest

from app.orchestration.registry import (
    AgentRegistry,
)
from app.orchestration.state import (
    AgentNodeResult,
    CareerWorkflowState,
)


async def executor(
    _: CareerWorkflowState,
) -> AgentNodeResult:
    return AgentNodeResult(
        status="completed",
        output={"ok": True},
    )


def test_registers_agent() -> None:
    registry = AgentRegistry()

    registry.register(
        "resume_parser",
        executor,
    )

    assert registry.contains("resume_parser")


def test_reports_missing_agent() -> None:
    registry = AgentRegistry()

    errors = registry.validate_nodes(
        [
            "resume_parser",
            "resume_matching",
        ]
    )

    assert len(errors) == 2


def test_get_unknown_agent_raises() -> None:
    registry = AgentRegistry()

    with pytest.raises(KeyError):
        registry.get("cover_letter")
