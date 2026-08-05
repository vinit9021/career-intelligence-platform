"""Factuality validation for Resume Parser Agent output."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.resume_parsing import ResumeStructuredContent

_EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

_PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")

_IGNORED_CONTENT_KEYS = {
    "metadata",
    "warnings",
    "raw_text",
    "normalized_text",
    "parser_name",
    "parser_version",
}


class ResumeValidationResult(BaseModel):
    """Result produced by deterministic agent-output validation."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _normalized_digits(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def _flatten_values(
    value: Any,
    path: str = "",
) -> list[tuple[str, str]]:
    flattened: list[tuple[str, str]] = []

    if isinstance(value, dict):
        for key, child_value in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            flattened.extend(
                _flatten_values(
                    child_value,
                    child_path,
                )
            )

        return flattened

    if isinstance(value, list):
        for index, child_value in enumerate(value):
            flattened.extend(
                _flatten_values(
                    child_value,
                    f"{path}[{index}]",
                )
            )

        return flattened

    if isinstance(value, str) and value.strip():
        flattened.append(
            (
                path,
                value.strip(),
            )
        )

    return flattened


def _contains_meaningful_content(
    flattened_values: list[tuple[str, str]],
) -> bool:
    for path, value in flattened_values:
        path_parts = {part.casefold() for part in re.split(r"[.\[\]]+", path) if part}

        if path_parts & _IGNORED_CONTENT_KEYS:
            continue

        if len(value.strip()) >= 2:
            return True

    return False


def _validate_emails(
    resume_text: str,
    flattened_values: list[tuple[str, str]],
) -> list[str]:
    errors: list[str] = []

    source_emails = {match.group(0).casefold() for match in _EMAIL_PATTERN.finditer(resume_text)}

    for path, value in flattened_values:
        if "email" not in path.casefold():
            continue

        for output_email in _EMAIL_PATTERN.findall(value):
            if output_email.casefold() not in source_emails:
                errors.append(
                    "The agent produced an email address that is not present in the source resume."
                )

    return errors


def _validate_phone_numbers(
    resume_text: str,
    flattened_values: list[tuple[str, str]],
) -> list[str]:
    errors: list[str] = []

    source_phone_numbers = {
        _normalized_digits(match.group(0)) for match in _PHONE_PATTERN.finditer(resume_text)
    }

    for path, value in flattened_values:
        lowered_path = path.casefold()

        if "phone" not in lowered_path and "mobile" not in lowered_path:
            continue

        for output_phone in _PHONE_PATTERN.findall(value):
            normalized_output = _normalized_digits(output_phone)

            if normalized_output and normalized_output not in source_phone_numbers:
                errors.append(
                    "The agent produced a phone number that is not present in the source resume."
                )

    return errors


def _skill_warnings(
    resume_text: str,
    flattened_values: list[tuple[str, str]],
) -> list[str]:
    warnings: list[str] = []
    normalized_source = re.sub(
        r"[^a-z0-9+#.]+",
        " ",
        resume_text.casefold(),
    )

    for path, value in flattened_values:
        if "skill" not in path.casefold():
            continue

        normalized_skill = re.sub(
            r"[^a-z0-9+#.]+",
            " ",
            value.casefold(),
        ).strip()

        if normalized_skill and normalized_skill not in normalized_source:
            warnings.append(f"Skill requires manual evidence review: {value}")

    return warnings


def validate_resume_output(
    resume_text: str,
    result: ResumeStructuredContent,
) -> ResumeValidationResult:
    """Validate schema output against facts present in source text."""

    serialized_result = result.model_dump(
        mode="python",
    )

    flattened_values = _flatten_values(
        serialized_result,
    )

    errors: list[str] = []
    warnings: list[str] = []

    if not _contains_meaningful_content(flattened_values):
        errors.append("The agent returned no meaningful structured resume content.")

    errors.extend(
        _validate_emails(
            resume_text,
            flattened_values,
        )
    )

    errors.extend(
        _validate_phone_numbers(
            resume_text,
            flattened_values,
        )
    )

    warnings.extend(
        _skill_warnings(
            resume_text,
            flattened_values,
        )
    )

    return ResumeValidationResult(
        is_valid=not errors,
        errors=list(dict.fromkeys(errors)),
        warnings=list(dict.fromkeys(warnings)),
    )
