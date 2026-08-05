"""Deterministic ATS baseline and fallback tools."""

from __future__ import annotations

from typing import Any

from app.agents.ats_optimization.state import (
    ATSOptimizationBaseline,
    ATSOptimizationRequest,
    ATSOptimizationResult,
)


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        clean_value = value.strip()
        key = clean_value.casefold()

        if not clean_value or key in seen:
            continue

        seen.add(key)
        result.append(clean_value)

    return result


def _contains_content(value: Any) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, list):
        return bool(value)

    if isinstance(value, dict):
        return bool(value)

    return True


def _percentage(
    matched_count: int,
    missing_count: int,
) -> float:
    total = matched_count + missing_count

    if total == 0:
        return 100.0

    return round(
        matched_count / total * 100,
        2,
    )


def build_ats_baseline(
    request: ATSOptimizationRequest,
) -> ATSOptimizationBaseline:
    """Create a deterministic ATS baseline."""

    match = request.match_result
    resume_data = request.resume.model_dump(mode="python")

    existing_keywords = _deduplicate(
        [
            *match.matched_required_skills,
            *match.matched_preferred_skills,
            *match.matched_technologies,
            *match.matched_keywords,
        ]
    )

    missing_high_priority = _deduplicate(
        [
            *match.missing_required_skills,
            *match.missing_technologies,
            *match.missing_keywords,
        ]
    )

    missing_preferred = _deduplicate(list(match.missing_preferred_skills))

    matched_count = len(existing_keywords)

    missing_count = len(missing_high_priority) + len(missing_preferred)

    keyword_coverage_score = _percentage(
        matched_count,
        missing_count,
    )

    checked_sections = (
        "summary",
        "skills",
        "experience",
        "projects",
        "education",
    )

    complete_sections = [
        section for section in checked_sections if _contains_content(resume_data.get(section))
    ]

    section_gaps = [section for section in checked_sections if section not in complete_sections]

    section_completeness_score = round(
        len(complete_sections) / len(checked_sections) * 100,
        2,
    )

    baseline_score = round(
        0.70 * match.overall_match_score
        + 0.20 * keyword_coverage_score
        + 0.10 * section_completeness_score,
        2,
    )

    actions: list[str] = []

    if missing_high_priority:
        actions.append(
            "Review missing required skills, "
            "technologies, and ATS keywords. Add them "
            "only when the resume contains factual "
            "support."
        )

    if missing_preferred:
        actions.append("Review preferred keywords after all required-keyword improvements.")

    if "summary" in section_gaps:
        actions.append(
            "Add a concise professional summary using only supported experience and skills."
        )

    if "skills" in section_gaps:
        actions.append("Add a clearly labelled skills section.")

    if "experience" in section_gaps:
        actions.append("Add relevant experience before attempting job-specific optimization.")

    if "projects" in section_gaps:
        actions.append("Add relevant projects when factual project evidence is available.")

    if not actions:
        actions.append(
            "Improve keyword placement and bullet clarity without changing factual content."
        )

    warnings = list(match.warnings)

    if not request.resume_raw_text.strip():
        warnings.append(
            "Raw resume text was not supplied. Validation uses structured resume content."
        )

    return ATSOptimizationBaseline(
        baseline_score=baseline_score,
        keyword_coverage_score=(keyword_coverage_score),
        section_completeness_score=(section_completeness_score),
        existing_keywords=existing_keywords,
        missing_high_priority_keywords=(missing_high_priority),
        missing_preferred_keywords=(missing_preferred),
        section_gaps=section_gaps,
        deterministic_actions=_deduplicate(actions),
        warnings=_deduplicate(warnings),
    )


def build_ats_fallback_result(
    baseline: ATSOptimizationBaseline,
) -> ATSOptimizationResult:
    """Convert the baseline into a safe fallback."""

    fallback_warning = (
        "AI ATS optimization was unavailable or invalid. "
        "The deterministic ATS baseline was returned."
    )

    return ATSOptimizationResult(
        baseline_score=baseline.baseline_score,
        projected_ats_score=baseline.baseline_score,
        projected_score_gain=0.0,
        keyword_coverage_score=(baseline.keyword_coverage_score),
        section_completeness_score=(baseline.section_completeness_score),
        existing_keywords=list(baseline.existing_keywords),
        missing_high_priority_keywords=list(baseline.missing_high_priority_keywords),
        missing_preferred_keywords=list(baseline.missing_preferred_keywords),
        safe_keywords_to_add=[],
        conditional_keywords=list(baseline.missing_high_priority_keywords),
        summary_rewrite=None,
        bullet_rewrites=[],
        section_recommendations=[],
        prioritized_actions=list(baseline.deterministic_actions),
        warnings=_deduplicate(
            [
                *baseline.warnings,
                fallback_warning,
            ]
        ),
        deterministic_fallback=True,
    )
