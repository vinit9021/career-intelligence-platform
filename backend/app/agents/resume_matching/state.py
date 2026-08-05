"""State and models for the Resume Matching AI Agent."""

from __future__ import annotations

import json
from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from app.schemas.resume_matching import (
    ResumeJobMatchRequest,
    ResumeJobMatchResult,
)

ResumeMatchingAgentStatus = Literal[
    "pending",
    "baselining",
    "analyzing",
    "validating",
    "retrying",
    "completed",
    "completed_with_fallback",
    "failed",
]

SemanticResponsibilityStatus = Literal[
    "aligned",
    "partially_aligned",
    "not_aligned",
]


class SemanticRequirementEvidence(BaseModel):
    """Semantic evidence connecting a requirement to the resume."""

    requirement: str = Field(min_length=1)
    resume_excerpt: str = Field(min_length=1)
    source_section: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class SemanticResponsibilityAssessment(BaseModel):
    """Semantic assessment for one job responsibility."""

    responsibility: str = Field(min_length=1)
    status: SemanticResponsibilityStatus
    score: float = Field(ge=0, le=100)
    resume_excerpt: str | None = None
    explanation: str = Field(min_length=1)


class SemanticResumeMatchingAnalysis(BaseModel):
    """Structured result returned by the Groq matching agent."""

    overall_semantic_score: float = Field(
        ge=0,
        le=100,
    )
    semantic_requirement_evidence: list[SemanticRequirementEvidence] = Field(default_factory=list)
    responsibility_alignment: list[SemanticResponsibilityAssessment] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)


class ResumeMatchingAgentInput(BaseModel):
    """Input supplied to the Resume Matching AI Agent."""

    request: ResumeJobMatchRequest
    baseline_result: ResumeJobMatchResult
    validation_feedback: list[str] = Field(default_factory=list)

    def to_prompt_payload(self) -> dict[str, str]:
        """Convert input into prompt-template variables."""

        feedback = (
            "\n".join(f"- {message}" for message in self.validation_feedback)
            or "No validation feedback is available."
        )

        return {
            "resume_json": json.dumps(
                self.request.resume.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            ),
            "resume_raw_text": (self.request.resume_raw_text or "No additional raw resume text."),
            "job_description_json": json.dumps(
                self.request.job_description.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            ),
            "baseline_json": json.dumps(
                self.baseline_result.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            ),
            "validation_feedback": feedback,
        }


class ResumeMatchingAgentState(
    TypedDict,
    total=False,
):
    """Shared LangGraph state for resume matching."""

    request: ResumeJobMatchRequest
    baseline_result: ResumeJobMatchResult | None
    agent_result: SemanticResumeMatchingAnalysis | None
    final_result: ResumeJobMatchResult | None
    attempt_count: int
    max_attempts: int
    validation_errors: list[str]
    warnings: list[str]
    status: ResumeMatchingAgentStatus
    last_error: str | None


class ResumeMatchingAgentWorkflowResult(BaseModel):
    """Final result returned by the workflow."""

    status: ResumeMatchingAgentStatus
    match_result: ResumeJobMatchResult | None = None
    semantic_analysis: SemanticResumeMatchingAnalysis | None = None
    attempt_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    last_error: str | None = None
