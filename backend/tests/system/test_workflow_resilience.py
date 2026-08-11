"""System-level retry and failure regression tests."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from app.orchestration.real_agents import RealAgentWorkflows
from app.workflow_execution.models import WorkflowExecutionRequest
from tests.system.conftest import (
    SystemAgentResult,
    build_success_workflows,
    build_system_service,
)


@pytest.mark.asyncio
async def test_agent_retry_recovers() -> None:
    """Transient agent failures are retried."""

    attempts = 0

    async def unstable_parser(
        *,
        text: str,
    ) -> SystemAgentResult:
        nonlocal attempts

        attempts += 1

        assert text

        if attempts == 1:
            raise RuntimeError("temporary parser failure")

        return SystemAgentResult(resume={"skills": ["Python"]})

    workflows = replace(
        build_success_workflows([]),
        resume_parser=unstable_parser,
    )

    service = build_system_service(workflows)

    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="retry-user",
            session_id="retry-session",
            resume_raw_text=("Python developer"),
            job_description_text=("Backend Engineer"),
            enabled_nodes=["resume_parser"],
            max_retries=1,
        )
    )

    assert result.status == "completed"

    assert attempts == 2

    assert result.retry_counts["resume_parser"] == 1

    assert result.steps[0].status == "completed"


@pytest.mark.asyncio
async def test_permanent_agent_failure_is_structured() -> None:
    """Permanent failures stop the workflow safely."""

    async def failing_parser(
        *,
        text: str,
    ) -> SystemAgentResult:
        assert text

        raise RuntimeError("permanent parser failure")

    workflows = replace(
        build_success_workflows([]),
        resume_parser=failing_parser,
    )

    service = build_system_service(workflows)

    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="failure-user",
            session_id="failure-session",
            resume_raw_text="Resume",
            job_description_text="JD",
            enabled_nodes=[
                "resume_parser",
                "job_description_analyzer",
                "resume_matching",
            ],
            max_retries=0,
        )
    )

    assert result.status == "failed"

    assert result.failed_node == "resume_parser"

    assert result.steps[0].status == "failed"

    assert result.steps[1].status == "skipped"

    assert result.steps[2].status == "skipped"

    assert result.errors

    assert any("permanent parser failure" in error for error in result.errors)


@pytest.mark.asyncio
async def test_missing_upstream_dependency_fails() -> None:
    """Dependent agents cannot run without required outputs."""

    workflows = build_success_workflows([])

    service = build_system_service(workflows)

    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="dependency-user",
            session_id=("dependency-session"),
            resume_raw_text="Resume",
            job_description_text="JD",
            enabled_nodes=["resume_matching"],
            max_retries=0,
        )
    )

    assert result.status == "failed"

    assert result.failed_node == "resume_matching"

    assert result.errors

    assert any("Resume Parser output" in error for error in result.errors)


@pytest.mark.asyncio
async def test_agent_warning_reaches_final_result() -> None:
    """Agent warnings propagate through orchestration."""

    async def warning_parser(
        *,
        text: str,
    ) -> SystemAgentResult:
        assert text

        return SystemAgentResult(
            resume={"skills": ["Python"]},
            warnings=[("Parser used deterministic fallback.")],
        )

    workflows: RealAgentWorkflows = replace(
        build_success_workflows([]),
        resume_parser=warning_parser,
    )

    service = build_system_service(workflows)

    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="warning-user",
            session_id=("warning-session"),
            resume_raw_text="Python",
            job_description_text="Backend",
            enabled_nodes=["resume_parser"],
        )
    )

    assert result.status == "completed"

    assert any("deterministic fallback" in warning.lower() for warning in result.warnings)


@pytest.mark.asyncio
async def test_result_outputs_remain_serializable() -> None:
    """Pydantic agent outputs are converted to safe state values."""

    class CustomOutput(SystemAgentResult):
        extra_data: dict[str, Any] = {"source": "system-test"}

    async def parser(
        *,
        text: str,
    ) -> CustomOutput:
        assert text

        return CustomOutput(resume={"skills": ["Python"]})

    workflows = replace(
        build_success_workflows([]),
        resume_parser=parser,
    )

    service = build_system_service(workflows)

    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="serial-user",
            session_id="serial-session",
            resume_raw_text="Python",
            job_description_text="Backend",
            enabled_nodes=["resume_parser"],
        )
    )

    assert result.status == "completed"

    assert isinstance(
        result.outputs["resume_parser"],
        dict,
    )
