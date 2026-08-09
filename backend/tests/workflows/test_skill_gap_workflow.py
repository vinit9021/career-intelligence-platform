"""Tests for Skill Gap Agent workflow."""

from __future__ import annotations

from typing import Any, cast

import pytest
from langchain_core.runnables import (
    RunnableLambda,
)

from app.agents.skill_gap.agent import (
    SkillGapRunnable,
)
from app.agents.skill_gap.state import (
    SkillGapAnalysis,
    SkillGapItem,
)
from app.workflows.skill_gap import (
    run_skill_gap_workflow,
)
from tests.agents.test_skill_gap_agent import (
    build_request,
    valid_analysis,
)


def successful_runnable() -> SkillGapRunnable:
    async def invoke(
        _: dict[str, Any],
    ) -> SkillGapAnalysis:
        return valid_analysis()

    return cast(
        SkillGapRunnable,
        RunnableLambda(invoke),
    )


@pytest.mark.asyncio
async def test_workflow_returns_skill_gap_analysis() -> None:
    result = await run_skill_gap_workflow(
        request=build_request(),
        runnable=successful_runnable(),
    )

    assert result.status == "completed"

    assert result.skill_gap is not None

    assert result.skill_gap.deterministic_fallback is False

    skills = {gap.skill for gap in result.skill_gap.gaps}

    assert "Kubernetes" in skills

    assert "Docker" in skills


@pytest.mark.asyncio
async def test_workflow_retries_false_gap() -> None:
    call_count = 0

    async def invoke(
        _: dict[str, Any],
    ) -> SkillGapAnalysis:
        nonlocal call_count

        call_count += 1

        analysis = valid_analysis()

        if call_count == 1:
            return analysis.model_copy(
                update={
                    "gaps": [
                        *analysis.gaps,
                        SkillGapItem(
                            skill="Python",
                            category=("required_skill"),
                            priority="critical",
                            reason=("Python is missing."),
                            jd_evidence="Python",
                        ),
                    ]
                }
            )

        return analysis

    runnable = cast(
        SkillGapRunnable,
        RunnableLambda(invoke),
    )

    result = await run_skill_gap_workflow(
        request=build_request(),
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed"

    assert result.attempt_count == 2

    assert call_count == 2


@pytest.mark.asyncio
async def test_workflow_uses_fallback_on_failure() -> None:
    async def invoke(
        _: dict[str, Any],
    ) -> SkillGapAnalysis:
        raise RuntimeError("Temporary Groq failure")

    runnable = cast(
        SkillGapRunnable,
        RunnableLambda(invoke),
    )

    result = await run_skill_gap_workflow(
        request=build_request(),
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed_with_fallback"

    assert result.attempt_count == 2

    assert result.skill_gap is not None

    assert result.skill_gap.deterministic_fallback is True


@pytest.mark.asyncio
async def test_workflow_respects_project_limit() -> None:
    request = build_request().model_copy(update={"max_mini_projects": 1})

    result = await run_skill_gap_workflow(
        request=request,
        runnable=successful_runnable(),
    )

    assert result.skill_gap is not None

    assert len(result.skill_gap.mini_projects) <= 1
