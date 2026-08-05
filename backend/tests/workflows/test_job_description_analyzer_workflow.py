"""Tests for the Job Description Analyzer workflow."""

from __future__ import annotations

from typing import Any, cast

import pytest
from langchain_core.runnables import RunnableLambda

from app.agents.job_description_analyzer.agent import (
    JobDescriptionAnalyzerRunnable,
)
from app.parsers import JobDescriptionParser
from app.schemas.job_description_parser import ParsedJobDescription
from app.workflows.job_description_analyzer import (
    run_job_description_analyzer_workflow,
)

JOB_DESCRIPTION_TEXT = """
Software Engineer

We Dolat Capital are looking for a Software Engineer
with 2+ years of experience.

Required skills:
- Python
- FastAPI
- PostgreSQL
- Git

Preferred skills:
- Docker
- AWS

Responsibilities:
- Develop backend APIs
- Write unit tests
- Review code

Education:
Bachelor's degree in Computer Science or a related field.
""".strip()


def _valid_result() -> ParsedJobDescription:
    parsed = JobDescriptionParser().parse(JOB_DESCRIPTION_TEXT)

    return parsed.model_copy(
        update={
            "company_name": "Dolat Capital",
        }
    )


def _successful_runnable() -> JobDescriptionAnalyzerRunnable:
    async def invoke(
        _: dict[str, Any],
    ) -> ParsedJobDescription:
        return _valid_result()

    return cast(
        JobDescriptionAnalyzerRunnable,
        RunnableLambda(invoke),
    )


@pytest.mark.asyncio
async def test_workflow_returns_ai_result() -> None:
    result = await run_job_description_analyzer_workflow(
        job_description_text=JOB_DESCRIPTION_TEXT,
        runnable=_successful_runnable(),
    )

    assert result.status == "completed"
    assert result.analyzed_job is not None
    assert result.analyzed_job.company_name == "Dolat Capital"
    assert result.attempt_count == 1
    assert result.analyzed_job.metadata.parser_name == "groq_job_description_analyzer"


@pytest.mark.asyncio
async def test_workflow_retries_invalid_company() -> None:
    call_count = 0

    async def invoke(
        _: dict[str, Any],
    ) -> ParsedJobDescription:
        nonlocal call_count
        call_count += 1

        result = _valid_result()

        if call_count == 1:
            return result.model_copy(
                update={
                    "company_name": "Imaginary Labs",
                }
            )

        return result

    runnable = cast(
        JobDescriptionAnalyzerRunnable,
        RunnableLambda(invoke),
    )

    result = await run_job_description_analyzer_workflow(
        job_description_text=JOB_DESCRIPTION_TEXT,
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed"
    assert result.attempt_count == 2
    assert call_count == 2
    assert result.analyzed_job is not None
    assert result.analyzed_job.company_name == "Dolat Capital"


@pytest.mark.asyncio
async def test_workflow_uses_fallback_after_failure() -> None:
    async def invoke(
        _: dict[str, Any],
    ) -> ParsedJobDescription:
        raise RuntimeError("Temporary Groq failure")

    runnable = cast(
        JobDescriptionAnalyzerRunnable,
        RunnableLambda(invoke),
    )

    result = await run_job_description_analyzer_workflow(
        job_description_text=JOB_DESCRIPTION_TEXT,
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed_with_fallback"
    assert result.attempt_count == 2
    assert result.analyzed_job is not None
    assert any("deterministic parser" in warning.casefold() for warning in result.warnings)


@pytest.mark.asyncio
async def test_short_input_is_rejected() -> None:
    call_count = 0

    async def invoke(
        _: dict[str, Any],
    ) -> ParsedJobDescription:
        nonlocal call_count
        call_count += 1
        return _valid_result()

    runnable = cast(
        JobDescriptionAnalyzerRunnable,
        RunnableLambda(invoke),
    )

    result = await run_job_description_analyzer_workflow(
        job_description_text="Python developer",
        runnable=runnable,
    )

    assert result.status == "failed"
    assert result.analyzed_job is None
    assert call_count == 0
    assert result.last_error is not None
