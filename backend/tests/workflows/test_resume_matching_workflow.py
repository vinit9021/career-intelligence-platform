"""Tests for the Resume Matching LangGraph workflow."""

from __future__ import annotations

from typing import Any, cast

import pytest
from langchain_core.runnables import RunnableLambda

from app.agents.resume_matching.agent import (
    ResumeMatchingRunnable,
)
from app.agents.resume_matching.state import (
    SemanticRequirementEvidence,
    SemanticResponsibilityAssessment,
    SemanticResumeMatchingAnalysis,
)
from app.schemas.job_description_parser import (
    JobDescriptionParserMetadata,
    JobExperienceRequirement,
    ParsedJobDescription,
)
from app.schemas.resume_matching import (
    ResumeJobMatchRequest,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)
from app.workflows.resume_matching import (
    run_resume_matching_workflow,
)


def build_request() -> ResumeJobMatchRequest:
    resume = ResumeStructuredContent.model_validate(
        {
            "summary": "Backend engineer.",
            "skills": [
                "Python",
                "AWS",
            ],
            "experience": [("Deployed backend services on AWS for production workloads.")],
            "education": [],
            "projects": [],
            "certifications": [],
        }
    )

    job = ParsedJobDescription(
        job_title="Backend Engineer",
        company_name="Example Labs",
        required_skills=[
            "Python",
            "Cloud deployment",
        ],
        preferred_skills=[],
        technologies=[
            "AWS",
        ],
        responsibilities=[("Deploy backend services to cloud infrastructure")],
        qualifications=[],
        experience=JobExperienceRequirement(),
        education_requirements=[],
        seniority_level="unspecified",
        ats_keywords=[
            "Python",
            "Cloud deployment",
        ],
        normalized_text=("Backend Engineer requiring Python, AWS and cloud deployment."),
        metadata=JobDescriptionParserMetadata(
            parser_name="test",
            parser_version="1.0.0",
            character_count=80,
        ),
    )

    return ResumeJobMatchRequest(
        resume=resume,
        job_description=job,
        resume_raw_text=("Deployed backend services on AWS for production workloads."),
    )


def valid_analysis() -> SemanticResumeMatchingAnalysis:
    return SemanticResumeMatchingAnalysis(
        overall_semantic_score=85,
        semantic_requirement_evidence=[
            SemanticRequirementEvidence(
                requirement="Cloud deployment",
                resume_excerpt=("Deployed backend services on AWS for production workloads."),
                source_section="experience",
                explanation=("The resume demonstrates cloud deployment through AWS."),
                confidence=0.9,
            )
        ],
        responsibility_alignment=[
            SemanticResponsibilityAssessment.model_validate(
                {
                    "responsibility": ("Deploy backend services to cloud infrastructure"),
                    "status": "aligned",
                    "score": 90,
                    "resume_excerpt": (
                        "Deployed backend services on AWS for production workloads."
                    ),
                    "explanation": ("The evidence directly supports the responsibility."),
                }
            )
        ],
        strengths=["Strong cloud deployment evidence."],
        weaknesses=[],
        warnings=[],
        summary="Strong semantic alignment.",
    )


def successful_runnable() -> ResumeMatchingRunnable:
    async def invoke(
        _: dict[str, Any],
    ) -> SemanticResumeMatchingAnalysis:
        return valid_analysis()

    return cast(
        ResumeMatchingRunnable,
        RunnableLambda(invoke),
    )


@pytest.mark.asyncio
async def test_workflow_returns_hybrid_result() -> None:
    result = await run_resume_matching_workflow(
        request=build_request(),
        runnable=successful_runnable(),
    )

    assert result.status == "completed"
    assert result.match_result is not None
    assert result.attempt_count == 1

    assert "Cloud deployment" in result.match_result.matched_required_skills

    assert "Cloud deployment" not in result.match_result.missing_required_skills

    assert result.match_result.metadata.engine_name == "hybrid_groq_resume_matching_agent"

    assert result.match_result.metadata.deterministic is False


@pytest.mark.asyncio
async def test_workflow_retries_invalid_output() -> None:
    call_count = 0

    async def invoke(
        _: dict[str, Any],
    ) -> SemanticResumeMatchingAnalysis:
        nonlocal call_count
        call_count += 1

        analysis = valid_analysis()

        if call_count == 1:
            invalid_evidence = analysis.semantic_requirement_evidence[0].model_copy(
                update={"resume_excerpt": ("Managed Kubernetes clusters.")}
            )

            return analysis.model_copy(update={"semantic_requirement_evidence": [invalid_evidence]})

        return analysis

    runnable = cast(
        ResumeMatchingRunnable,
        RunnableLambda(invoke),
    )

    result = await run_resume_matching_workflow(
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
    ) -> SemanticResumeMatchingAnalysis:
        raise RuntimeError("Temporary Groq failure")

    runnable = cast(
        ResumeMatchingRunnable,
        RunnableLambda(invoke),
    )

    result = await run_resume_matching_workflow(
        request=build_request(),
        runnable=runnable,
        max_attempts=2,
    )

    assert result.status == "completed_with_fallback"
    assert result.match_result is not None
    assert result.attempt_count == 2
    assert result.match_result.metadata.deterministic is True
    assert any(
        "deterministic matching result" in warning.casefold()
        for warning in result.match_result.warnings
    )
