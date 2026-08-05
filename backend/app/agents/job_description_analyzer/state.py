"""State models for the Job Description Analyzer Agent."""

from __future__ import annotations

import json
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

from app.schemas.job_description_parser import ParsedJobDescription

JobDescriptionAnalyzerStatus = Literal[
    "pending",
    "normalizing",
    "baselining",
    "analyzing",
    "validating",
    "retrying",
    "completed",
    "completed_with_fallback",
    "failed",
]


class JobDescriptionAnalyzerInput(BaseModel):
    """Input supplied to the Job Description Analyzer Agent."""

    job_description_text: str = Field(min_length=20)
    baseline_result: dict[str, Any] = Field(default_factory=dict)
    validation_feedback: list[str] = Field(default_factory=list)

    def to_prompt_payload(self) -> dict[str, str]:
        """Convert input into prompt variables."""

        feedback = (
            "\n".join(f"- {message}" for message in self.validation_feedback)
            or "No validation feedback is available."
        )

        return {
            "job_description_text": self.job_description_text,
            "baseline_json": json.dumps(
                self.baseline_result,
                indent=2,
                sort_keys=True,
                default=str,
            ),
            "validation_feedback": feedback,
        }


class JobDescriptionAnalyzerState(TypedDict, total=False):
    """Shared LangGraph state."""

    job_description_text: str
    normalized_text: str
    baseline_result: dict[str, Any]
    agent_result: ParsedJobDescription | None
    final_result: ParsedJobDescription | None
    attempt_count: int
    max_attempts: int
    validation_errors: list[str]
    warnings: list[str]
    status: JobDescriptionAnalyzerStatus
    last_error: str | None


class JobDescriptionAnalyzerWorkflowResult(BaseModel):
    """Final workflow result."""

    status: JobDescriptionAnalyzerStatus
    analyzed_job: ParsedJobDescription | None = None
    attempt_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    last_error: str | None = None
