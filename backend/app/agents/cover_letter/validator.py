"""Validation for Cover Letter AI output."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from app.agents.cover_letter.state import (
    CoverLetterAnalysis,
    CoverLetterRequest,
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]+")

_NUMBER_PATTERN = re.compile(r"(?<![a-zA-Z])\d+(?:\.\d+)?%?")


class CoverLetterValidationResult(BaseModel):
    """Validation result for generated cover letter."""

    is_valid: bool

    errors: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)


def _normalize(value: str) -> str:
    return " ".join(_TOKEN_PATTERN.findall(value.casefold()))


def _deduplicate(
    values: list[str],
) -> list[str]:
    return list(dict.fromkeys(values))


def _resume_corpus(
    request: CoverLetterRequest,
) -> str:
    structured_resume = json.dumps(
        request.resume.model_dump(mode="json"),
        default=str,
    )

    return _normalize(structured_resume + "\n" + request.resume_raw_text)


def _job_keywords(
    request: CoverLetterRequest,
) -> dict[str, str]:
    job = request.job_description

    values = [
        *job.required_skills,
        *job.preferred_skills,
        *job.technologies,
        *job.ats_keywords,
    ]

    return {_normalize(value): value for value in values if _normalize(value)}


def _numbers(value: str) -> set[str]:
    return set(_NUMBER_PATTERN.findall(value))


def _word_count(value: str) -> int:
    return len(value.split())


def _claim_overlap(
    claim: str,
    evidence: str,
) -> float:
    claim_tokens = set(_normalize(claim).split())

    evidence_tokens = set(_normalize(evidence).split())

    if not claim_tokens:
        return 0.0

    return len(claim_tokens & evidence_tokens) / len(claim_tokens)


def validate_cover_letter_output(
    request: CoverLetterRequest,
    result: CoverLetterAnalysis,
) -> CoverLetterValidationResult:
    """Validate cover-letter claims against resume."""

    errors: list[str] = []
    warnings: list[str] = []

    resume_corpus = _resume_corpus(request)

    job_keywords = _job_keywords(request)

    full_text = result.full_text()

    normalized_letter = _normalize(full_text)

    for item in result.evidence:
        normalized_excerpt = _normalize(item.resume_excerpt)

        if not normalized_excerpt or normalized_excerpt not in resume_corpus:
            errors.append(
                f"Cover-letter evidence does not exist in the resume: {item.resume_excerpt}"
            )

        if (
            normalized_excerpt
            and _claim_overlap(
                item.claim,
                item.resume_excerpt,
            )
            < 0.20
        ):
            warnings.append(
                f"Cover-letter claim has weak lexical overlap with its evidence: {item.claim}"
            )

    seen_skills: set[str] = set()

    for skill in result.skills_mentioned:
        normalized_skill = _normalize(skill)

        if normalized_skill in seen_skills:
            warnings.append(f"Duplicate skill mention: {skill}")

        seen_skills.add(normalized_skill)

        if normalized_skill not in resume_corpus:
            errors.append(
                f"Cover letter mentions a skill that is not supported by the resume: {skill}"
            )

        if normalized_skill not in job_keywords:
            warnings.append(
                f"Cover letter mentions a skill that is not a target-job keyword: {skill}"
            )

    for normalized_keyword, keyword in job_keywords.items():
        if (
            normalized_keyword
            and normalized_keyword in normalized_letter
            and normalized_keyword not in resume_corpus
        ):
            errors.append(
                f"Cover letter uses an unsupported job keyword as candidate evidence: {keyword}"
            )

    resume_numbers = _numbers(
        json.dumps(
            request.resume.model_dump(mode="json"),
            default=str,
        )
        + " "
        + request.resume_raw_text
    )

    added_numbers = _numbers(full_text) - resume_numbers

    if added_numbers:
        errors.append(
            "Cover letter introduces unsupported "
            "numeric claims or metrics: " + ", ".join(sorted(added_numbers))
        )

    if _word_count(full_text) > request.max_words:
        errors.append(f"Cover letter exceeds the requested {request.max_words}-word limit.")

    company_name = request.job_description.company_name

    if company_name and _normalize(company_name) not in normalized_letter:
        warnings.append("Company name is not mentioned in the cover letter.")

    job_title = request.job_description.job_title

    if job_title and _normalize(job_title) not in normalized_letter:
        warnings.append("Job title is not mentioned in the cover letter.")

    if not result.evidence:
        warnings.append("Cover letter contains no explicit resume evidence mappings.")

    return CoverLetterValidationResult(
        is_valid=not errors,
        errors=_deduplicate(errors),
        warnings=_deduplicate(warnings),
    )
