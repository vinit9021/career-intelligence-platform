"""State and schemas for Skill Gap AI Agent."""

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

GapCategory = Literal[
    "required_skill",
    "preferred_skill",
    "technology",
    "knowledge",
]

GapPriority = Literal[
    "critical",
    "high",
    "medium",
    "low",
]

GapDifficulty = Literal[
    "beginner",
    "intermediate",
    "advanced",
]

LearningEffort = Literal[
    "short",
    "medium",
    "long",
]

SkillGapStatus = Literal[
    "pending",
    "analyzing",
    "validating",
    "retrying",
    "completed",
    "completed_with_fallback",
    "failed",
]


class SkillGapItem(BaseModel):
    """One identified candidate skill gap."""

    skill: str = Field(min_length=1)

    category: GapCategory

    priority: GapPriority

    reason: str = Field(min_length=1)

    jd_evidence: str = Field(min_length=1)

    difficulty: GapDifficulty = "intermediate"

    estimated_effort: LearningEffort = "medium"


class LearningRoadmapStep(BaseModel):
    """Learning step for one missing skill."""

    order: int = Field(ge=1)

    target_skill: str = Field(min_length=1)

    topics: list[str] = Field(
        min_length=1,
        max_length=8,
    )

    exercises: list[str] = Field(
        min_length=1,
        max_length=6,
    )

    completion_signal: str = Field(min_length=1)


class MiniProjectRecommendation(BaseModel):
    """Practical mini-project for skill development."""

    title: str = Field(min_length=1)

    target_skills: list[str] = Field(
        min_length=1,
        max_length=5,
    )

    description: str = Field(min_length=1)

    deliverables: list[str] = Field(
        min_length=1,
        max_length=6,
    )


class SkillGapAnalysis(BaseModel):
    """Structured Groq analysis."""

    gap_score: float = Field(
        ge=0,
        le=100,
    )

    gaps: list[SkillGapItem] = Field(default_factory=list)

    learning_roadmap: list[LearningRoadmapStep] = Field(default_factory=list)

    mini_projects: list[MiniProjectRecommendation] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)

    summary: str = Field(min_length=1)


class SkillGapRequest(BaseModel):
    """Input for Skill Gap Agent."""

    resume: ResumeStructuredContent

    job_description: ParsedJobDescription

    match_result: ResumeJobMatchResult

    resume_raw_text: str = ""

    max_roadmap_steps: int = Field(
        default=8,
        ge=1,
        le=15,
    )

    max_mini_projects: int = Field(
        default=3,
        ge=0,
        le=6,
    )


class SkillGapBaseline(BaseModel):
    """Deterministic skill-gap baseline."""

    gap_score: float = Field(
        ge=0,
        le=100,
    )

    matched_skills: list[str] = Field(default_factory=list)

    missing_required_skills: list[str] = Field(default_factory=list)

    missing_preferred_skills: list[str] = Field(default_factory=list)

    missing_technologies: list[str] = Field(default_factory=list)

    deterministic_gaps: list[SkillGapItem] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)


class SkillGapAgentInput(BaseModel):
    """Prompt input for Groq."""

    request: SkillGapRequest

    baseline: SkillGapBaseline

    validation_feedback: list[str] = Field(default_factory=list)

    def to_prompt_payload(self) -> dict[str, str]:
        """Convert agent input to prompt variables."""

        feedback = (
            "\n".join(f"- {item}" for item in self.validation_feedback) or "No validation feedback."
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
            "max_roadmap_steps": str(self.request.max_roadmap_steps),
            "max_mini_projects": str(self.request.max_mini_projects),
            "validation_feedback": feedback,
        }


class SkillGapResult(BaseModel):
    """Final Skill Gap Agent result."""

    gap_score: float = Field(
        ge=0,
        le=100,
    )

    matched_skills: list[str] = Field(default_factory=list)

    gaps: list[SkillGapItem] = Field(default_factory=list)

    learning_roadmap: list[LearningRoadmapStep] = Field(default_factory=list)

    mini_projects: list[MiniProjectRecommendation] = Field(default_factory=list)

    summary: str

    warnings: list[str] = Field(default_factory=list)

    agent_name: str = "groq_skill_gap_agent"

    agent_version: str = "1.0.0"

    deterministic_fallback: bool = False


class SkillGapState(
    TypedDict,
    total=False,
):
    """Shared LangGraph workflow state."""

    request: SkillGapRequest

    baseline: SkillGapBaseline | None

    agent_result: SkillGapAnalysis | None

    final_result: SkillGapResult | None

    attempt_count: int

    max_attempts: int

    validation_errors: list[str]

    warnings: list[str]

    status: SkillGapStatus

    last_error: str | None


class SkillGapWorkflowResult(BaseModel):
    """Result returned by the LangGraph workflow."""

    status: SkillGapStatus

    skill_gap: SkillGapResult | None = None

    agent_analysis: SkillGapAnalysis | None = None

    baseline: SkillGapBaseline | None = None

    attempt_count: int = 0

    validation_errors: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)

    last_error: str | None = None
