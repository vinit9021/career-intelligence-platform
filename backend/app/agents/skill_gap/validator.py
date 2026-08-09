"""Evidence validation for Skill Gap Agent."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from app.agents.skill_gap.state import (
    SkillGapAnalysis,
    SkillGapBaseline,
    SkillGapRequest,
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]+")


class SkillGapValidationResult(BaseModel):
    """Validation result."""

    is_valid: bool

    errors: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)


def _normalize(value: str) -> str:
    return " ".join(_TOKEN_PATTERN.findall(value.casefold()))


def _deduplicate(
    values: list[str],
) -> list[str]:
    return list(dict.fromkeys(values))


def _job_corpus(
    request: SkillGapRequest,
) -> str:
    return _normalize(
        json.dumps(
            request.job_description.model_dump(mode="json"),
            default=str,
        )
    )


def _allowed_missing_skills(
    baseline: SkillGapBaseline,
) -> dict[str, str]:
    values = [
        *baseline.missing_required_skills,
        *baseline.missing_preferred_skills,
        *baseline.missing_technologies,
    ]

    return {_normalize(value): value for value in values if _normalize(value)}


def validate_skill_gap_output(
    request: SkillGapRequest,
    baseline: SkillGapBaseline,
    result: SkillGapAnalysis,
) -> SkillGapValidationResult:
    """Reject false or unsupported skill gaps."""

    errors: list[str] = []
    warnings: list[str] = []

    allowed = _allowed_missing_skills(baseline)

    job_corpus = _job_corpus(request)

    seen_gaps: set[str] = set()

    for gap in result.gaps:
        skill = _normalize(gap.skill)

        if skill in seen_gaps:
            errors.append(f"Duplicate skill gap: {gap.skill}")

        seen_gaps.add(skill)

        if skill not in allowed:
            errors.append(f"Agent identified a false or unsupported skill gap: {gap.skill}")

        evidence = _normalize(gap.jd_evidence)

        if not evidence or evidence not in job_corpus:
            errors.append(
                f"Job-description evidence does not exist in the source JD: {gap.jd_evidence}"
            )

    for step in result.learning_roadmap:
        target = _normalize(step.target_skill)

        if target not in allowed:
            errors.append(
                f"Learning roadmap targets a skill that is not a validated gap: {step.target_skill}"
            )

    if len(result.learning_roadmap) > request.max_roadmap_steps:
        errors.append("Learning roadmap exceeds the requested maximum number of steps.")

    for project in result.mini_projects:
        for skill in project.target_skills:
            normalized_skill = _normalize(skill)

            if normalized_skill not in allowed:
                errors.append(f"Mini-project targets a skill that is not a validated gap: {skill}")

    if len(result.mini_projects) > request.max_mini_projects:
        errors.append("Mini-project recommendations exceed the requested maximum.")

    baseline_missing = set(allowed)

    missing_from_analysis = baseline_missing - seen_gaps

    if missing_from_analysis:
        warnings.append(
            "Agent omitted some deterministic skill "
            "gaps; they will be restored in the "
            "final result."
        )

    return SkillGapValidationResult(
        is_valid=not errors,
        errors=_deduplicate(errors),
        warnings=_deduplicate(warnings),
    )
