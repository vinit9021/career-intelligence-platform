"""Tests for deterministic ATS optimization tools."""

from app.ats.optimizer import (
    build_ats_baseline,
    build_ats_fallback_result,
)
from tests.agents.test_ats_optimization_agent import (
    build_request,
)


def test_baseline_detects_missing_keyword() -> None:
    baseline = build_ats_baseline(build_request())

    assert "Kubernetes" in (baseline.missing_high_priority_keywords)
    assert baseline.baseline_score >= 0
    assert baseline.baseline_score <= 100


def test_fallback_preserves_baseline() -> None:
    baseline = build_ats_baseline(build_request())

    result = build_ats_fallback_result(baseline)

    assert result.deterministic_fallback is True
    assert result.projected_ats_score == baseline.baseline_score
    assert result.projected_score_gain == 0
    assert any("deterministic ats baseline" in warning.casefold() for warning in result.warnings)
