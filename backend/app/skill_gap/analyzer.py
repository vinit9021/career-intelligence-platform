"""Deterministic Skill Gap baseline and fallback."""

from __future__ import annotations

import json
import re

from app.agents.skill_gap.state import (
    LearningRoadmapStep,
    MiniProjectRecommendation,
    SkillGapBaseline,
    SkillGapItem,
    SkillGapRequest,
    SkillGapResult,
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9+#.]+")


def _normalize(value: str) -> str:
    return " ".join(_TOKEN_PATTERN.findall(value.casefold()))


def _deduplicate(
    values: list[str],
) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        key = _normalize(value)

        if not key or key in seen:
            continue

        seen.add(key)
        result.append(value)

    return result


def _resume_corpus(
    request: SkillGapRequest,
) -> str:
    return _normalize(
        json.dumps(
            request.resume.model_dump(mode="json"),
            default=str,
        )
        + "\n"
        + request.resume_raw_text
    )


def _is_supported(
    skill: str,
    resume_corpus: str,
) -> bool:
    normalized_skill = _normalize(skill)

    return bool(normalized_skill and normalized_skill in resume_corpus)


def _make_gap(
    *,
    skill: str,
    category: str,
    priority: str,
    reason: str,
) -> SkillGapItem:
    return SkillGapItem.model_validate(
        {
            "skill": skill,
            "category": category,
            "priority": priority,
            "reason": reason,
            "jd_evidence": skill,
            "difficulty": "intermediate",
            "estimated_effort": "medium",
        }
    )


def build_skill_gap_baseline(
    request: SkillGapRequest,
) -> SkillGapBaseline:
    """Build deterministic resume/JD gap baseline."""

    resume_corpus = _resume_corpus(request)

    job = request.job_description

    required = _deduplicate(list(job.required_skills))

    preferred = _deduplicate(list(job.preferred_skills))

    technologies = _deduplicate(list(job.technologies))

    missing_required = [
        skill
        for skill in required
        if not _is_supported(
            skill,
            resume_corpus,
        )
    ]

    missing_preferred = [
        skill
        for skill in preferred
        if not _is_supported(
            skill,
            resume_corpus,
        )
    ]

    missing_technologies = [
        skill
        for skill in technologies
        if not _is_supported(
            skill,
            resume_corpus,
        )
    ]

    matched = _deduplicate(
        [
            *[
                skill
                for skill in required
                if _is_supported(
                    skill,
                    resume_corpus,
                )
            ],
            *[
                skill
                for skill in preferred
                if _is_supported(
                    skill,
                    resume_corpus,
                )
            ],
            *[
                skill
                for skill in technologies
                if _is_supported(
                    skill,
                    resume_corpus,
                )
            ],
        ]
    )

    gaps: list[SkillGapItem] = []

    for skill in missing_required:
        gaps.append(
            _make_gap(
                skill=skill,
                category="required_skill",
                priority="critical",
                reason=(
                    "The job description lists this "
                    "as a required skill, but it is "
                    "not supported by the resume."
                ),
            )
        )

    required_keys = {_normalize(skill) for skill in required}

    for skill in missing_technologies:
        if _normalize(skill) in required_keys:
            continue

        gaps.append(
            _make_gap(
                skill=skill,
                category="technology",
                priority="high",
                reason=("The role uses this technology, but resume evidence was not found."),
            )
        )

    known_gap_keys = {_normalize(gap.skill) for gap in gaps}

    for skill in missing_preferred:
        if _normalize(skill) in known_gap_keys:
            continue

        gaps.append(
            _make_gap(
                skill=skill,
                category="preferred_skill",
                priority="medium",
                reason=(
                    "The job description lists this "
                    "as preferred, but resume evidence "
                    "was not found."
                ),
            )
        )

    total_weight = len(required) * 3 + len(technologies) * 2 + len(preferred)

    missing_weight = (
        len(missing_required) * 3 + len(missing_technologies) * 2 + len(missing_preferred)
    )

    gap_score = (
        0.0
        if total_weight == 0
        else min(
            100.0,
            round(
                (missing_weight / total_weight) * 100,
                2,
            ),
        )
    )

    warnings: list[str] = []

    match_data = request.match_result.model_dump(mode="python")

    if not match_data:
        warnings.append("Resume-job match result contained no structured data.")

    return SkillGapBaseline(
        gap_score=gap_score,
        matched_skills=matched,
        missing_required_skills=(missing_required),
        missing_preferred_skills=(missing_preferred),
        missing_technologies=(missing_technologies),
        deterministic_gaps=gaps,
        warnings=warnings,
    )


def build_skill_gap_fallback(
    baseline: SkillGapBaseline,
    request: SkillGapRequest,
) -> SkillGapResult:
    """Create safe deterministic fallback."""

    roadmap: list[LearningRoadmapStep] = []

    for index, gap in enumerate(
        baseline.deterministic_gaps[: request.max_roadmap_steps],
        start=1,
    ):
        roadmap.append(
            LearningRoadmapStep(
                order=index,
                target_skill=gap.skill,
                topics=[(f"Core concepts and practical usage of {gap.skill}")],
                exercises=[(f"Complete one focused hands-on exercise using {gap.skill}.")],
                completion_signal=(
                    f"Explain and demonstrate {gap.skill} in a small working example."
                ),
            )
        )

    projects: list[MiniProjectRecommendation] = []

    if request.max_mini_projects > 0:
        for gap in baseline.deterministic_gaps[: request.max_mini_projects]:
            projects.append(
                MiniProjectRecommendation(
                    title=(f"{gap.skill} Practice Project"),
                    target_skills=[gap.skill],
                    description=(f"Build a small practical project focused on {gap.skill}."),
                    deliverables=[
                        "Working implementation",
                        "Short README",
                        "Demonstration of the target skill",
                    ],
                )
            )

    return SkillGapResult(
        gap_score=baseline.gap_score,
        matched_skills=(baseline.matched_skills),
        gaps=baseline.deterministic_gaps,
        learning_roadmap=roadmap,
        mini_projects=projects,
        summary=(
            "Deterministic skill-gap analysis generated from resume and job description evidence."
        ),
        warnings=[
            *baseline.warnings,
            (
                "Groq Skill Gap Agent was unavailable "
                "or returned invalid output. "
                "Deterministic recommendations "
                "were used."
            ),
        ],
        deterministic_fallback=True,
    )
