"""Tests for central Career Intelligence LangGraph."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import pytest

from app.orchestration.graph import (
    run_career_workflow,
)
from app.orchestration.registry import (
    AgentRegistry,
)
from app.orchestration.state import (
    AgentNodeResult,
    CareerWorkflowRequest,
    CareerWorkflowState,
)


def success_executor(
    name: str,
) -> Callable[
    [CareerWorkflowState],
    Awaitable[AgentNodeResult],
]:
    async def execute(
        _: CareerWorkflowState,
    ) -> AgentNodeResult:
        return AgentNodeResult(
            status="completed",
            output={
                "agent": name,
            },
        )

    return execute


async def register_core(
    registry: AgentRegistry,
) -> None:
    registry.register(
        "resume_parser",
        success_executor("resume_parser"),
    )

    registry.register(
        "job_description_analyzer",
        success_executor("job_description_analyzer"),
    )

    registry.register(
        "resume_matching",
        success_executor("resume_matching"),
    )

    registry.register(
        "ats_optimization",
        success_executor("ats_optimization"),
    )

    registry.register(
        "skill_gap",
        success_executor("skill_gap"),
    )

    registry.register(
        "cover_letter",
        success_executor("cover_letter"),
    )


@pytest.mark.asyncio
async def test_executes_agents_in_order() -> None:
    registry = AgentRegistry()

    await register_core(registry)

    result = await run_career_workflow(
        registry=registry,
        request=CareerWorkflowRequest(
            enabled_nodes=[
                "resume_parser",
                "job_description_analyzer",
                "resume_matching",
            ]
        ),
    )

    assert result.status == "completed"

    assert result.execution_order == [
        "resume_parser",
        "job_description_analyzer",
        "resume_matching",
    ]

    assert "resume_matching" in (result.outputs)


@pytest.mark.asyncio
async def test_skips_disabled_nodes() -> None:
    registry = AgentRegistry()

    registry.register(
        "resume_parser",
        success_executor("resume_parser"),
    )

    registry.register(
        "skill_gap",
        success_executor("skill_gap"),
    )

    result = await run_career_workflow(
        registry=registry,
        request=CareerWorkflowRequest(
            enabled_nodes=[
                "resume_parser",
                "skill_gap",
            ]
        ),
    )

    assert result.status == "completed"

    assert result.execution_order == [
        "resume_parser",
        "skill_gap",
    ]


@pytest.mark.asyncio
async def test_retries_failed_agent() -> None:
    registry = AgentRegistry()

    calls = 0

    async def flaky(
        _: CareerWorkflowState,
    ) -> AgentNodeResult:
        nonlocal calls

        calls += 1

        if calls == 1:
            return AgentNodeResult(
                status="failed",
                error="temporary failure",
                retryable=True,
            )

        return AgentNodeResult(
            status="completed",
            output={
                "parsed": True,
            },
        )

    registry.register(
        "resume_parser",
        flaky,
    )

    result = await run_career_workflow(
        registry=registry,
        request=CareerWorkflowRequest(enabled_nodes=["resume_parser"]),
        max_retries=1,
    )

    assert result.status == "completed"

    assert calls == 2

    assert result.retry_counts["resume_parser"] == 1


@pytest.mark.asyncio
async def test_uses_fallback_after_retries() -> None:
    registry = AgentRegistry()

    primary_calls = 0
    fallback_calls = 0

    async def failing(
        _: CareerWorkflowState,
    ) -> AgentNodeResult:
        nonlocal primary_calls

        primary_calls += 1

        return AgentNodeResult(
            status="failed",
            error="primary unavailable",
            retryable=True,
        )

    async def fallback(
        _: CareerWorkflowState,
    ) -> AgentNodeResult:
        nonlocal fallback_calls

        fallback_calls += 1

        return AgentNodeResult(
            status="completed",
            output={"source": "fallback"},
        )

    registry.register(
        "resume_parser",
        failing,
        fallback=fallback,
    )

    result = await run_career_workflow(
        registry=registry,
        request=CareerWorkflowRequest(enabled_nodes=["resume_parser"]),
        max_retries=1,
    )

    assert result.status == "completed"

    assert primary_calls == 2

    assert fallback_calls == 1

    assert result.fallback_nodes == ["resume_parser"]

    assert result.outputs["resume_parser"]["source"] == "fallback"


@pytest.mark.asyncio
async def test_fails_without_fallback() -> None:
    registry = AgentRegistry()

    async def failing(
        _: CareerWorkflowState,
    ) -> AgentNodeResult:
        return AgentNodeResult(
            status="failed",
            error="permanent failure",
            retryable=False,
        )

    registry.register(
        "resume_parser",
        failing,
    )

    result = await run_career_workflow(
        registry=registry,
        request=CareerWorkflowRequest(enabled_nodes=["resume_parser"]),
    )

    assert result.status == "failed"

    assert result.failed_node == ("resume_parser")

    assert "permanent failure" in (result.errors)


@pytest.mark.asyncio
async def test_fails_for_missing_registration() -> None:
    registry = AgentRegistry()

    result = await run_career_workflow(
        registry=registry,
        request=CareerWorkflowRequest(enabled_nodes=["resume_parser"]),
    )

    assert result.status == "failed"

    assert result.errors

    assert "not registered" in result.errors[0]


@pytest.mark.asyncio
async def test_supports_resume_version_node() -> None:
    registry = AgentRegistry()

    registry.register(
        "resume_version_manager",
        success_executor("resume_version_manager"),
    )

    result = await run_career_workflow(
        registry=registry,
        request=CareerWorkflowRequest(enabled_nodes=["resume_version_manager"]),
    )

    assert result.status == "completed"

    assert result.execution_order == ["resume_version_manager"]
