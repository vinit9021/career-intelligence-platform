"""Tests for deterministic Skill Gap tools."""

from app.skill_gap.analyzer import (
    build_skill_gap_baseline,
    build_skill_gap_fallback,
)
from tests.agents.test_skill_gap_agent import (
    build_request,
)


def test_baseline_detects_missing_skills() -> None:
    baseline = build_skill_gap_baseline(build_request())

    assert "Kubernetes" in (baseline.missing_required_skills)

    assert "Docker" in (baseline.missing_technologies)

    assert "Redis" in (baseline.missing_preferred_skills)


def test_baseline_does_not_mark_existing_skill() -> None:
    baseline = build_skill_gap_baseline(build_request())

    assert "Python" in (baseline.matched_skills)

    missing = {gap.skill for gap in baseline.deterministic_gaps}

    assert "Python" not in missing


def test_fallback_generates_roadmap() -> None:
    request = build_request()

    baseline = build_skill_gap_baseline(request)

    result = build_skill_gap_fallback(
        baseline,
        request,
    )

    assert result.deterministic_fallback is True

    assert result.gaps

    assert result.learning_roadmap

    assert len(result.mini_projects) <= request.max_mini_projects
