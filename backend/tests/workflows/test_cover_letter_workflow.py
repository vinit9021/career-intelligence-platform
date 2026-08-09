"""Tests for Cover Letter Agent workflow."""

from __future__ import annotations

from typing import Any, cast

import pytest
from langchain_core.runnables import (
    RunnableLambda,
)

from app.agents.cover_letter.agent import (
    CoverLetterRunnable,
)
from app.agents.cover_letter.state import (
    CoverLetterAnalysis,
)
from app.workflows.cover_letter import (
    run_cover_letter_workflow,
)
from tests.agents.test_cover_letter_agent import (
    build_request,
    valid_analysis,
)


def successful_runnable() -> CoverLetterRunnable:
    async def invoke(
        _: dict[str, Any],
    ) -> CoverLetterAnalysis:
        return valid_analysis()

    return cast(
        CoverLetterRunnable,
        RunnableLambda(invoke),
    )


@pytest.mark.asyncio
async def test_workflow_returns_cover_letter() -> None:
    result = await run_cover_letter_workflow(
        request=build_request(),
        runnable=successful_runnable(),
    )

    assert result.status == "completed"
    assert result.cover_letter is not None
    assert result.attempt_count == 1

    assert result.cover_letter.deterministic_fallback is False

    assert "Example Labs" in (result.cover_letter.full_text)


@pytest.mark.asyncio
async def test_workflow_retries_invalid_skill() -> None:
    call_count = 0

    async def invoke(
        _: dict[str, Any],
    ) -> CoverLetterAnalysis:
        nonlocal call_count

        call_count += 1

        analysis = valid_analysis()

        if call_count == 1:
            return analysis.model_copy(
                update={
                    "skills_mentioned": [
                        *analysis.skills_mentioned,
                        "Kubernetes",
                    ],
                    "body_paragraphs": [("I have Kubernetes production experience.")],
                }
            )

        return analysis

    runnable = cast(
        CoverLetterRunnable,
        RunnableLambda(invoke),
    )

    result = await run_cover_letter_workflow(
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
    ) -> CoverLetterAnalysis:
        raise RuntimeError("Temporary Groq failure")

    runnable = cast(
        CoverLetterRunnable,
        RunnableLambda(invoke),
    )

    result = await run_cover_letter_workflow(
        request=build_request(),
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed_with_fallback"

    assert result.attempt_count == 2
    assert result.cover_letter is not None

    assert result.cover_letter.deterministic_fallback is True
