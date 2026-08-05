"""Validation for Job Description Analyzer output."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.schemas.job_description_parser import ParsedJobDescription

_TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]+")

_TITLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "of",
    "the",
    "to",
}

_SKILL_ALIASES = (
    {
        "amazon web services",
        "aws",
    },
    {
        "javascript",
        "js",
    },
    {
        "kubernetes",
        "k8s",
    },
    {
        "postgres",
        "postgresql",
    },
    {
        "rest api",
        "rest APIs",
        "restful api",
        "restful APIs",
    },
)


class JobDescriptionValidationResult(BaseModel):
    """Result of validating the agent output."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _normalize(value: str) -> str:
    return " ".join(_TOKEN_PATTERN.findall(value.casefold()))


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _phrase_supported(
    value: str,
    source_text: str,
) -> bool:
    normalized_value = _normalize(value)
    normalized_source = _normalize(source_text)

    if not normalized_value:
        return False

    if normalized_value in normalized_source:
        return True

    for aliases in _SKILL_ALIASES:
        normalized_aliases = {_normalize(alias) for alias in aliases}

        if normalized_value not in normalized_aliases:
            continue

        if any(alias in normalized_source for alias in normalized_aliases):
            return True

    return False


def _title_supported(
    title: str,
    source_text: str,
) -> bool:
    if _phrase_supported(title, source_text):
        return True

    title_tokens = {token for token in _normalize(title).split() if token not in _TITLE_STOPWORDS}

    source_tokens = set(_normalize(source_text).split())

    if not title_tokens:
        return False

    overlap = len(title_tokens & source_tokens) / len(title_tokens)

    return overlap >= 0.6


def _responsibility_supported(
    responsibility: str,
    source_text: str,
) -> bool:
    responsibility_tokens = set(_normalize(responsibility).split())

    source_tokens = set(_normalize(source_text).split())

    if not responsibility_tokens:
        return False

    overlap = len(responsibility_tokens & source_tokens) / len(responsibility_tokens)

    return overlap >= 0.35


def _validate_values(
    source_text: str,
    values: list[str],
    label: str,
) -> list[str]:
    warnings: list[str] = []

    for value in values:
        if _phrase_supported(value, source_text):
            continue

        warnings.append(f"{label} requires evidence review: {value}")

    return warnings


def validate_job_description_output(
    source_text: str,
    result: ParsedJobDescription,
) -> JobDescriptionValidationResult:
    """Validate AI output against the source JD."""

    errors: list[str] = []
    warnings: list[str] = []

    meaningful_content = any(
        (
            result.job_title,
            result.company_name,
            result.required_skills,
            result.preferred_skills,
            result.responsibilities,
        )
    )

    if not meaningful_content:
        errors.append("The agent returned no meaningful job information.")

    if result.company_name and not _phrase_supported(
        result.company_name,
        source_text,
    ):
        errors.append("The extracted company name is not supported by the source job description.")

    if result.job_title and not _title_supported(
        result.job_title,
        source_text,
    ):
        warnings.append("The extracted job title requires evidence review.")

    warnings.extend(
        _validate_values(
            source_text,
            result.required_skills,
            "Required skill",
        )
    )

    warnings.extend(
        _validate_values(
            source_text,
            result.preferred_skills,
            "Preferred skill",
        )
    )

    warnings.extend(
        _validate_values(
            source_text,
            result.technologies,
            "Technology",
        )
    )

    warnings.extend(
        _validate_values(
            source_text,
            result.ats_keywords,
            "ATS keyword",
        )
    )

    for responsibility in result.responsibilities:
        if _responsibility_supported(
            responsibility,
            source_text,
        ):
            continue

        warnings.append(f"Responsibility requires evidence review: {responsibility}")

    return JobDescriptionValidationResult(
        is_valid=not errors,
        errors=_deduplicate(errors),
        warnings=_deduplicate(warnings),
    )
