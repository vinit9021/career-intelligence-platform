"""Tests for Resume Version Manager binding."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from app.orchestration.production import (
    run_real_career_workflow,
)
from app.orchestration.real_agents import (
    RealAgentWorkflows,
)


class VersionResult(BaseModel):
    status: str = "completed"
    version: Any = None


class VersionRequest(BaseModel):
    operation: str


@pytest.mark.asyncio
async def test_version_manager_can_be_registered() -> None:
    agent_object = object()

    async def version_runner(
        *,
        agent: Any,
        request: VersionRequest,
    ) -> VersionResult:
        assert agent is agent_object

        assert request.operation == "create"

        return VersionResult(version={"version_number": 2})

    async def unused(
        **_: Any,
    ) -> VersionResult:
        return VersionResult()

    workflows = RealAgentWorkflows(
        resume_parser=unused,
        job_description_analyzer=unused,
        resume_matching=unused,
        ats_optimization=unused,
        skill_gap=unused,
        cover_letter=unused,
        resume_version_manager=(version_runner),
    )

    result = await run_real_career_workflow(
        resume_raw_text="Resume",
        job_description_text="JD",
        workflows=workflows,
        enabled_nodes=["resume_version_manager"],
        include_resume_version_manager=True,
        extra_context={
            "resume_version_agent": (agent_object),
            "resume_version_request": (VersionRequest(operation="create")),
        },
    )

    assert result.status == "completed"

    assert result.outputs["resume_version_manager"]["version_number"] == 2
