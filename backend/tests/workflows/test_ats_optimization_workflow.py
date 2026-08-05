"""Tests for the ATS Optimization LangGraph workflow."""

from __future__ import annotations

from typing import Any, cast

import pytest
from langchain_core.runnables import RunnableLambda

from app.agents.ats_optimization.agent import (
    ATSOptimizationRunnable,
)
from app.agents.ats_optimization.state import (
    ATSOptimizationAnalysis,
)
from app.workflows.ats_optimization import (
    run_ats_optimization_workflow,
)
from tests.agents.test_ats_optimization_agent import (
    build_request,
    valid_analysis,
)


def successful_runnable() -> ATSOptimizationRunnable:
    async def invoke(
        _: dict[str, Any],
    ) -> ATSOptimizationAnalysis:
        return valid_analysis()

    return cast(
        ATSOptimizationRunnable,
        RunnableLambda(invoke),
    )


@pytest.mark.asyncio
async def test_workflow_returns_optimization() -> None:
    result = await run_ats_optimization_workflow(
        request=build_request(),
        runnable=successful_runnable(),
    )

    assert result.status == "completed"
    assert result.optimization_result is not None
    assert result.attempt_count == 1
    assert result.optimization_result.deterministic_fallback is False
    assert "Kubernetes" in (result.optimization_result.conditional_keywords)
    assert "AWS" in (result.optimization_result.safe_keywords_to_add)


@pytest.mark.asyncio
async def test_workflow_retries_invalid_metric() -> None:
    call_count = 0

    async def invoke(
        _: dict[str, Any],
    ) -> ATSOptimizationAnalysis:
        nonlocal call_count
        call_count += 1

        analysis = valid_analysis()

        if call_count == 1:
            invalid_rewrite = analysis.bullet_rewrites[0].model_copy(
                update={
                    "rewritten_text": (
                        "Improved latency by 50% while deploying backend services on AWS."
                    )
                }
            )

            return analysis.model_copy(update={"bullet_rewrites": [invalid_rewrite]})

        return analysis

    runnable = cast(
        ATSOptimizationRunnable,
        RunnableLambda(invoke),
    )

    result = await run_ats_optimization_workflow(
        request=build_request(),
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed"
    assert result.attempt_count == 2
    assert call_count == 2


@pytest.mark.asyncio
async def test_workflow_uses_fallback() -> None:
    async def invoke(
        _: dict[str, Any],
    ) -> ATSOptimizationAnalysis:
        raise RuntimeError("Temporary Groq failure")

    runnable = cast(
        ATSOptimizationRunnable,
        RunnableLambda(invoke),
    )

    result = await run_ats_optimization_workflow(
        request=build_request(),
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed_with_fallback"
    assert result.attempt_count == 2
    assert result.optimization_result is not None
    assert result.optimization_result.deterministic_fallback is True
    assert result.optimization_result.projected_score_gain == 0
