"""Tests for real agent orchestration adapters."""

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


class MatchRequest(BaseModel):
    resume: dict[str, Any]
    job_description: dict[str, Any]
    resume_raw_text: str


class ATSRequest(BaseModel):
    resume: dict[str, Any]
    job_description: dict[str, Any]
    match_result: dict[str, Any]
    resume_raw_text: str
    max_bullet_rewrites: int = 5


class SkillGapRequest(BaseModel):
    resume: dict[str, Any]
    job_description: dict[str, Any]
    match_result: dict[str, Any]
    resume_raw_text: str
    max_roadmap_steps: int = 8
    max_mini_projects: int = 3


class CoverLetterRequest(BaseModel):
    resume: dict[str, Any]
    job_description: dict[str, Any]
    match_result: dict[str, Any]
    resume_raw_text: str
    candidate_name: str | None = None
    company_context: str | None = None
    tone: str = "professional"
    max_words: int = 300


class Result(BaseModel):
    status: str = "completed"
    resume: Any = None
    job_description: Any = None
    match_result: Any = None
    optimization: Any = None
    skill_gap: Any = None
    cover_letter: Any = None
    warnings: list[str] = []


def build_workflows(
    calls: list[str],
) -> RealAgentWorkflows:
    async def resume_parser(
        *,
        text: str,
    ) -> Result:
        calls.append("resume_parser")

        assert "Python" in text

        return Result(
            resume={
                "skills": ["Python"],
                "summary": "Backend engineer",
            }
        )

    async def jd_analyzer(
        *,
        text: str,
    ) -> Result:
        calls.append("job_description_analyzer")

        assert "Backend" in text

        return Result(
            job_description={
                "job_title": ("Backend Engineer"),
                "required_skills": ["Python"],
            }
        )

    async def resume_matching(
        *,
        request: MatchRequest,
    ) -> Result:
        calls.append("resume_matching")

        assert request.resume["skills"] == ["Python"]

        assert request.job_description["job_title"] == "Backend Engineer"

        return Result(match_result={"overall_match_score": 90})

    async def ats(
        *,
        request: ATSRequest,
    ) -> Result:
        calls.append("ats_optimization")

        assert request.match_result["overall_match_score"] == 90

        return Result(optimization={"ats_score": 92})

    async def skill_gap(
        *,
        request: SkillGapRequest,
    ) -> Result:
        calls.append("skill_gap")

        assert request.match_result["overall_match_score"] == 90

        return Result(skill_gap={"gaps": []})

    async def cover_letter(
        *,
        request: CoverLetterRequest,
    ) -> Result:
        calls.append("cover_letter")

        assert request.candidate_name == "Alex"

        return Result(cover_letter={"full_text": ("Dear Hiring Team")})

    return RealAgentWorkflows(
        resume_parser=resume_parser,
        job_description_analyzer=(jd_analyzer),
        resume_matching=resume_matching,
        ats_optimization=ats,
        skill_gap=skill_gap,
        cover_letter=cover_letter,
    )


@pytest.mark.asyncio
async def test_real_agents_handoff_outputs() -> None:
    calls: list[str] = []

    result = await run_real_career_workflow(
        resume_raw_text=("Backend engineer using Python."),
        job_description_text=("Backend Engineer requiring Python."),
        workflows=build_workflows(calls),
        extra_context={"candidate_name": "Alex"},
    )

    assert result.status == "completed"

    assert result.execution_order == [
        "resume_parser",
        "job_description_analyzer",
        "resume_matching",
        "ats_optimization",
        "skill_gap",
        "cover_letter",
    ]

    assert calls == (result.execution_order)

    assert result.outputs["resume_matching"]["overall_match_score"] == 90

    assert result.outputs["ats_optimization"]["ats_score"] == 92


@pytest.mark.asyncio
async def test_real_agents_support_optional_nodes() -> None:
    calls: list[str] = []

    result = await run_real_career_workflow(
        resume_raw_text=("Backend engineer using Python."),
        job_description_text=("Backend Engineer requiring Python."),
        workflows=build_workflows(calls),
        enabled_nodes=[
            "resume_parser",
            "job_description_analyzer",
            "resume_matching",
        ],
    )

    assert result.status == "completed"

    assert calls == [
        "resume_parser",
        "job_description_analyzer",
        "resume_matching",
    ]


@pytest.mark.asyncio
async def test_missing_dependency_fails_cleanly() -> None:
    calls: list[str] = []

    result = await run_real_career_workflow(
        resume_raw_text=("Backend engineer using Python."),
        job_description_text=("Backend Engineer requiring Python."),
        workflows=build_workflows(calls),
        enabled_nodes=["resume_matching"],
        max_retries=0,
    )

    assert result.status == "failed"

    assert result.failed_node == ("resume_matching")

    assert result.last_error is not None

    assert "Resume Parser output" in result.last_error
