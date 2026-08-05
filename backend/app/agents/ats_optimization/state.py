"""State and structured models for ATS optimization."""

from __future__ import annotations

import json
from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from app.schemas.job_description_parser import (
    ParsedJobDescription,
)
from app.schemas.resume_matching import (
    ResumeJobMatchResult,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)

ATSPriority = Literal[
    "high",
    "medium",
    "low",
]

ATSOptimizationStatus = Literal[
    "pending",
    "baselining",
    "analyzing",
    "validating",
    "retrying",
    "completed",
    "completed_with_fallback",
    "failed",
]


class ATSOptimizationRequest(BaseModel):
    """Input required by the ATS Optimization Agent."""

    resume: ResumeStructuredContent
    job_description: ParsedJobDescription
    match_result: ResumeJobMatchResult
    resume_raw_text: str = ""
    max_bullet_rewrites: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class ATSOptimizationBaseline(BaseModel):
    """Deterministic ATS baseline analysis."""

    baseline_score: float = Field(
        ge=0,
        le=100,
    )
    keyword_coverage_score: float = Field(
        ge=0,
        le=100,
    )
    section_completeness_score: float = Field(
        ge=0,
        le=100,
    )
    existing_keywords: list[str] = Field(default_factory=list)
    missing_high_priority_keywords: list[str] = Field(default_factory=list)
    missing_preferred_keywords: list[str] = Field(default_factory=list)
    section_gaps: list[str] = Field(default_factory=list)
    deterministic_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ATSKeywordRecommendation(BaseModel):
    """Recommendation for one job-related keyword."""

    keyword: str = Field(min_length=1)
    priority: ATSPriority
    target_section: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    currently_supported_by_resume: bool
    safe_to_add: bool
    resume_evidence: str | None = None


class ATSSummaryRewrite(BaseModel):
    """Evidence-grounded resume summary rewrite."""

    original_summary: str
    rewritten_summary: str = Field(min_length=1)
    keywords_added: list[str] = Field(default_factory=list)
    evidence_excerpts: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)


class ATSBulletRewrite(BaseModel):
    """Evidence-grounded experience or project rewrite."""

    source_section: Literal[
        "experience",
        "projects",
    ]
    original_text: str = Field(min_length=1)
    rewritten_text: str = Field(min_length=1)
    keywords_added: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)


class ATSSectionRecommendation(BaseModel):
    """Improvement recommendation for a resume section."""

    section: str = Field(min_length=1)
    priority: ATSPriority
    issue: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)


class ATSOptimizationAnalysis(BaseModel):
    """Structured output returned by the Groq agent."""

    proposed_ats_score: float = Field(
        ge=0,
        le=100,
    )
    keyword_recommendations: list[ATSKeywordRecommendation] = Field(default_factory=list)
    summary_rewrite: ATSSummaryRewrite | None = None
    bullet_rewrites: list[ATSBulletRewrite] = Field(default_factory=list)
    section_recommendations: list[ATSSectionRecommendation] = Field(default_factory=list)
    prioritized_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)


class ATSOptimizationResult(BaseModel):
    """Final validated ATS optimization result."""

    baseline_score: float = Field(
        ge=0,
        le=100,
    )
    projected_ats_score: float = Field(
        ge=0,
        le=100,
    )
    projected_score_gain: float = Field(
        ge=0,
        le=100,
    )
    keyword_coverage_score: float = Field(
        ge=0,
        le=100,
    )
    section_completeness_score: float = Field(
        ge=0,
        le=100,
    )
    existing_keywords: list[str] = Field(default_factory=list)
    missing_high_priority_keywords: list[str] = Field(default_factory=list)
    missing_preferred_keywords: list[str] = Field(default_factory=list)
    safe_keywords_to_add: list[str] = Field(default_factory=list)
    conditional_keywords: list[str] = Field(default_factory=list)
    summary_rewrite: ATSSummaryRewrite | None = None
    bullet_rewrites: list[ATSBulletRewrite] = Field(default_factory=list)
    section_recommendations: list[ATSSectionRecommendation] = Field(default_factory=list)
    prioritized_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    agent_name: str = "groq_ats_optimization_agent"
    agent_version: str = "1.0.0"
    deterministic_fallback: bool = False


class ATSOptimizationAgentInput(BaseModel):
    """Prompt input supplied to the AI agent."""

    request: ATSOptimizationRequest
    baseline: ATSOptimizationBaseline
    validation_feedback: list[str] = Field(default_factory=list)

    def to_prompt_payload(self) -> dict[str, str]:
        """Convert models into prompt variables."""

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
            "match_result_json": json.dumps(
                self.request.match_result.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            ),
            "baseline_json": json.dumps(
                self.baseline.model_dump(mode="json"),
                indent=2,
                sort_keys=True,
            ),
            "max_bullet_rewrites": str(self.request.max_bullet_rewrites),
            "validation_feedback": feedback,
        }


class ATSOptimizationState(
    TypedDict,
    total=False,
):
    """Shared LangGraph state."""

    request: ATSOptimizationRequest
    baseline: ATSOptimizationBaseline | None
    agent_result: ATSOptimizationAnalysis | None
    final_result: ATSOptimizationResult | None
    attempt_count: int
    max_attempts: int
    validation_errors: list[str]
    warnings: list[str]
    status: ATSOptimizationStatus
    last_error: str | None


class ATSOptimizationWorkflowResult(BaseModel):
    """Final LangGraph execution result."""

    status: ATSOptimizationStatus
    optimization_result: ATSOptimizationResult | None = None
    agent_analysis: ATSOptimizationAnalysis | None = None
    attempt_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    last_error: str | None = None
