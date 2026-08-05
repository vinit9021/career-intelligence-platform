"""Validation for Resume Matching AI Agent output."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from app.agents.resume_matching.state import (
    SemanticResumeMatchingAnalysis,
)
from app.schemas.resume_matching import (
    ResumeJobMatchRequest,
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]+")


class ResumeMatchingValidationResult(BaseModel):
    """Validation result for semantic matching output."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _normalize(value: str) -> str:
    return " ".join(_TOKEN_PATTERN.findall(value.casefold()))


def _resume_corpus(
    request: ResumeJobMatchRequest,
) -> str:
    structured_text = json.dumps(
        request.resume.model_dump(mode="json"),
        default=str,
    )

    return _normalize(structured_text + "\n" + request.resume_raw_text)


def _allowed_requirements(
    request: ResumeJobMatchRequest,
) -> dict[str, str]:
    job = request.job_description

    requirements = [
        *job.required_skills,
        *job.preferred_skills,
        *job.technologies,
        *job.ats_keywords,
    ]

    return {
        _normalize(requirement): requirement
        for requirement in requirements
        if _normalize(requirement)
    }


def _allowed_responsibilities(
    request: ResumeJobMatchRequest,
) -> dict[str, str]:
    return {
        _normalize(responsibility): responsibility
        for responsibility in request.job_description.responsibilities
        if _normalize(responsibility)
    }


def validate_semantic_match_output(
    request: ResumeJobMatchRequest,
    result: SemanticResumeMatchingAnalysis,
) -> ResumeMatchingValidationResult:
    """Validate semantic evidence against source data."""

    errors: list[str] = []
    warnings: list[str] = []

    corpus = _resume_corpus(request)
    allowed_requirements = _allowed_requirements(request)
    allowed_responsibilities = _allowed_responsibilities(request)

    seen_requirements: set[str] = set()

    for evidence in result.semantic_requirement_evidence:
        normalized_requirement = _normalize(evidence.requirement)

        if normalized_requirement not in allowed_requirements:
            errors.append(
                "The agent analyzed a requirement that "
                "does not exist in the job description: "
                f"{evidence.requirement}"
            )

        if normalized_requirement in seen_requirements:
            warnings.append(f"Duplicate semantic requirement evidence: {evidence.requirement}")

        seen_requirements.add(normalized_requirement)

        normalized_excerpt = _normalize(evidence.resume_excerpt)

        if not normalized_excerpt or normalized_excerpt not in corpus:
            errors.append(
                "The semantic evidence excerpt is not "
                "supported by the resume: "
                f"{evidence.resume_excerpt}"
            )

        if evidence.confidence < 0.6:
            warnings.append(f"Low-confidence semantic evidence: {evidence.requirement}")

    seen_responsibilities: set[str] = set()

    for assessment in result.responsibility_alignment:
        normalized_responsibility = _normalize(assessment.responsibility)

        if normalized_responsibility not in allowed_responsibilities:
            errors.append(
                "The agent analyzed a responsibility "
                "that is not present in the job "
                "description: "
                f"{assessment.responsibility}"
            )

        if normalized_responsibility in seen_responsibilities:
            errors.append(
                f"The agent returned duplicate responsibility analysis: {assessment.responsibility}"
            )

        seen_responsibilities.add(normalized_responsibility)

        if assessment.resume_excerpt:
            normalized_excerpt = _normalize(assessment.resume_excerpt)

            if normalized_excerpt and normalized_excerpt not in corpus:
                errors.append(
                    "The responsibility evidence excerpt "
                    "is not supported by the resume: "
                    f"{assessment.resume_excerpt}"
                )

    missing_responsibilities = set(allowed_responsibilities) - seen_responsibilities

    if missing_responsibilities:
        warnings.append("The semantic agent did not analyze every job responsibility.")

    if not result.strengths:
        warnings.append("The semantic agent returned no strengths.")

    if not result.weaknesses:
        warnings.append("The semantic agent returned no weaknesses.")

    return ResumeMatchingValidationResult(
        is_valid=not errors,
        errors=list(dict.fromkeys(errors)),
        warnings=list(dict.fromkeys(warnings)),
    )
