"""Tests for inner-agent fallback propagation."""

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


class Result(BaseModel):
    status: str
    resume: Any = None
    warnings: list[str] = []


@pytest.mark.asyncio
async def test_completed_with_fallback_is_success() -> None:
    async def resume_parser(
        *,
        text: str,
    ) -> Result:
        assert text

        return Result(
            status=("completed_with_fallback"),
            resume={"skills": ["Python"]},
            warnings=[("Deterministic parser was used.")],
        )

    async def unused(
        **_: Any,
    ) -> Result:
        return Result(status="completed")

    workflows = RealAgentWorkflows(
        resume_parser=resume_parser,
        job_description_analyzer=unused,
        resume_matching=unused,
        ats_optimization=unused,
        skill_gap=unused,
        cover_letter=unused,
    )

    result = await run_real_career_workflow(
        resume_raw_text="Python developer",
        job_description_text=("Backend Engineer"),
        workflows=workflows,
        enabled_nodes=["resume_parser"],
    )

    assert result.status == "completed"

    assert result.outputs["resume_parser"]["skills"] == ["Python"]

    assert any("Deterministic parser" in warning for warning in result.warnings)
