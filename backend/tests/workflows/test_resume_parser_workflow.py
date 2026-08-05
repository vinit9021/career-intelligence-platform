"""Tests for the Resume Parser LangGraph workflow."""

from __future__ import annotations

from typing import Any, cast

import pytest
from langchain_core.runnables import RunnableLambda

from app.agents.resume_parser.agent import (
    ResumeParserRunnable,
)
from app.schemas.resume_parsing import ResumeStructuredContent
from app.workflows.resume_parser import (
    run_resume_parser_workflow,
)

LONG_RESUME_TEXT = """
Arnav Bhandari
arnav@example.com

Software Engineer experienced in Python backend development.
Skills include Python, FastAPI, PostgreSQL, Git, and Docker.
Developed REST APIs and wrote automated unit tests for services.
Bachelor of Technology in Computer Science.
""".strip()


def _structured_resume() -> ResumeStructuredContent:
    values: dict[str, Any] = {}

    model_fields = ResumeStructuredContent.model_fields

    if "summary" in model_fields:
        values["summary"] = "Software Engineer experienced in Python backend development."

    if "professional_summary" in model_fields:
        values["professional_summary"] = (
            "Software Engineer experienced in Python backend development."
        )

    if "skills" in model_fields:
        values["skills"] = [
            "Python",
            "FastAPI",
        ]

    if "raw_text" in model_fields:
        values["raw_text"] = LONG_RESUME_TEXT

    return ResumeStructuredContent.model_construct(**values)


def _successful_runnable() -> ResumeParserRunnable:
    async def invoke(
        _: dict[str, Any],
    ) -> ResumeStructuredContent:
        return _structured_resume()

    return cast(
        ResumeParserRunnable,
        RunnableLambda(invoke),
    )


@pytest.mark.asyncio
async def test_workflow_returns_structured_resume() -> None:
    result = await run_resume_parser_workflow(
        resume_text=LONG_RESUME_TEXT,
        runnable=_successful_runnable(),
    )

    assert result.status == "completed"
    assert result.structured_resume is not None
    assert result.attempt_count == 1
    assert result.requires_ocr is False


@pytest.mark.asyncio
async def test_workflow_retries_after_model_failure() -> None:
    call_count = 0

    async def invoke(
        _: dict[str, Any],
    ) -> ResumeStructuredContent:
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            raise RuntimeError("Temporary model failure")

        return _structured_resume()

    runnable = cast(
        ResumeParserRunnable,
        RunnableLambda(invoke),
    )

    result = await run_resume_parser_workflow(
        resume_text=LONG_RESUME_TEXT,
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed"
    assert result.attempt_count == 2
    assert call_count == 2


@pytest.mark.asyncio
async def test_workflow_routes_short_text_to_ocr() -> None:
    result = await run_resume_parser_workflow(
        resume_text="Scanned resume",
        runnable=_successful_runnable(),
    )

    assert result.status == "needs_ocr"
    assert result.requires_ocr is True
    assert result.structured_resume is None
    assert result.attempt_count == 0
