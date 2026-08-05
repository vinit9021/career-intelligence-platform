"""State and input models for the Resume Parser Agent."""

from __future__ import annotations

import json
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

from app.schemas.resume_parsing import ResumeStructuredContent

ResumeParserStatus = Literal[
    "pending",
    "assessing_text",
    "analyzing",
    "validating",
    "retrying",
    "completed",
    "completed_with_fallback",
    "needs_ocr",
    "failed",
]


class ResumeParserAgentInput(BaseModel):
    """Validated input passed to the Resume Parser Agent."""

    resume_text: str = Field(min_length=1)
    baseline_result: dict[str, Any] = Field(default_factory=dict)
    validation_feedback: list[str] = Field(default_factory=list)

    def to_prompt_payload(self) -> dict[str, str]:
        """Convert input into prompt-template variables."""

        feedback = (
            "\n".join(f"- {message}" for message in self.validation_feedback)
            or "No validation feedback is available."
        )

        return {
            "resume_text": self.resume_text,
            "baseline_json": json.dumps(
                self.baseline_result,
                indent=2,
                sort_keys=True,
                default=str,
            ),
            "validation_feedback": feedback,
        }


class ResumeParserState(TypedDict, total=False):
    """Shared LangGraph state for resume parsing."""

    resume_text: str
    baseline_result: dict[str, Any]
    agent_result: ResumeStructuredContent | None
    final_result: ResumeStructuredContent | None
    attempt_count: int
    max_attempts: int
    validation_errors: list[str]
    warnings: list[str]
    status: ResumeParserStatus
    last_error: str | None
    requires_ocr: bool


class ResumeParserWorkflowResult(BaseModel):
    """Final public result returned by the agent workflow."""

    status: ResumeParserStatus
    structured_resume: ResumeStructuredContent | None = None
    attempt_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    requires_ocr: bool = False
    last_error: str | None = None
