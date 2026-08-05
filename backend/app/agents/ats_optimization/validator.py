"""Validation for ATS Optimization AI output."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from app.agents.ats_optimization.state import (
    ATSOptimizationAnalysis,
    ATSOptimizationRequest,
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]+")
_NUMBER_PATTERN = re.compile(r"(?<![a-zA-Z])\d+(?:\.\d+)?%?")


class ATSOptimizationValidationResult(BaseModel):
    """Validation result for an optimization response."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _normalize(value: str) -> str:
    return " ".join(_TOKEN_PATTERN.findall(value.casefold()))


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _resume_corpus(
    request: ATSOptimizationRequest,
) -> str:
    structured_resume = json.dumps(
        request.resume.model_dump(mode="json"),
        default=str,
    )

    return _normalize(structured_resume + "\n" + request.resume_raw_text)


def _allowed_job_keywords(
    request: ATSOptimizationRequest,
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


def _validate_keyword(
    *,
    keyword: str,
    allowed_keywords: dict[str, str],
    errors: list[str],
    context: str,
) -> str:
    normalized_keyword = _normalize(keyword)

    if normalized_keyword not in allowed_keywords:
        errors.append(
            f"{context} contains a keyword that is not present in the job description: {keyword}"
        )

    return normalized_keyword


def _validate_rewrite_numbers(
    *,
    original_text: str,
    rewritten_text: str,
    errors: list[str],
    context: str,
    additional_evidence: str = "",
) -> None:
    supported_numbers = _numbers(original_text + " " + additional_evidence)

    added_numbers = _numbers(rewritten_text) - supported_numbers

    if added_numbers:
        values = ", ".join(sorted(added_numbers))

        errors.append(f"{context} introduces unsupported numeric claims or metrics: {values}")


def validate_ats_optimization_output(
    request: ATSOptimizationRequest,
    result: ATSOptimizationAnalysis,
) -> ATSOptimizationValidationResult:
    """Validate AI suggestions against source evidence."""

    errors: list[str] = []
    warnings: list[str] = []

    corpus = _resume_corpus(request)
    allowed_keywords = _allowed_job_keywords(request)

    seen_recommendations: set[str] = set()

    for item in result.keyword_recommendations:
        normalized_keyword = _validate_keyword(
            keyword=item.keyword,
            allowed_keywords=allowed_keywords,
            errors=errors,
            context="Keyword recommendation",
        )

        if normalized_keyword in seen_recommendations:
            warnings.append(f"Duplicate keyword recommendation: {item.keyword}")

        seen_recommendations.add(normalized_keyword)

        normalized_evidence = _normalize(item.resume_evidence or "")

        if item.safe_to_add:
            if not item.currently_supported_by_resume:
                errors.append(
                    "A keyword marked safe to add was "
                    "not marked as supported by the "
                    f"resume: {item.keyword}"
                )

            if not normalized_evidence or normalized_evidence not in corpus:
                errors.append(
                    "A keyword marked safe to add does "
                    "not contain valid resume evidence: "
                    f"{item.keyword}"
                )

        if item.currently_supported_by_resume and (
            not normalized_evidence or normalized_evidence not in corpus
        ):
            errors.append(f"Keyword support evidence does not exist in the resume: {item.keyword}")

    if result.summary_rewrite is not None:
        summary = result.summary_rewrite
        resume_data = request.resume.model_dump(mode="python")

        original_summary = str(resume_data.get("summary") or "")

        if _normalize(summary.original_summary) != _normalize(original_summary):
            errors.append("The supplied original summary does not match the resume summary.")

        valid_summary_evidence: list[str] = []

        for excerpt in summary.evidence_excerpts:
            normalized_excerpt = _normalize(excerpt)

            if not normalized_excerpt or normalized_excerpt not in corpus:
                errors.append(f"Summary rewrite evidence does not exist in the resume: {excerpt}")
            else:
                valid_summary_evidence.append(excerpt)

        for keyword in summary.keywords_added:
            normalized_keyword = _validate_keyword(
                keyword=keyword,
                allowed_keywords=allowed_keywords,
                errors=errors,
                context="Summary rewrite",
            )

            if normalized_keyword not in corpus:
                errors.append(
                    "Summary rewrite adds a job keyword "
                    "that is not supported by the "
                    f"resume: {keyword}"
                )

        _validate_rewrite_numbers(
            original_text=summary.original_summary,
            rewritten_text=summary.rewritten_summary,
            additional_evidence=" ".join(valid_summary_evidence),
            errors=errors,
            context="Summary rewrite",
        )

    if len(result.bullet_rewrites) > request.max_bullet_rewrites:
        errors.append("The agent returned more bullet rewrites than requested.")

    seen_bullets: set[str] = set()

    for rewrite in result.bullet_rewrites:
        normalized_original = _normalize(rewrite.original_text)

        if not normalized_original or normalized_original not in corpus:
            errors.append(
                f"Bullet rewrite source text does not exist in the resume: {rewrite.original_text}"
            )

        if normalized_original in seen_bullets:
            errors.append(f"Duplicate bullet rewrite detected: {rewrite.original_text}")

        seen_bullets.add(normalized_original)

        for keyword in rewrite.keywords_added:
            normalized_keyword = _validate_keyword(
                keyword=keyword,
                allowed_keywords=allowed_keywords,
                errors=errors,
                context="Bullet rewrite",
            )

            if normalized_keyword not in corpus:
                errors.append(
                    "Bullet rewrite adds a job keyword "
                    "that is not supported by the "
                    f"resume: {keyword}"
                )

        _validate_rewrite_numbers(
            original_text=rewrite.original_text,
            rewritten_text=rewrite.rewritten_text,
            errors=errors,
            context="Bullet rewrite",
        )

    if not result.prioritized_actions:
        warnings.append("The optimization agent returned no prioritized actions.")

    if not result.section_recommendations:
        warnings.append("The optimization agent returned no section recommendations.")

    return ATSOptimizationValidationResult(
        is_valid=not errors,
        errors=_deduplicate(errors),
        warnings=_deduplicate(warnings),
    )
