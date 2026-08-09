"""Tests for deterministic cover-letter fallback."""

from app.cover_letters.generator import (
    build_cover_letter_fallback,
)
from tests.agents.test_cover_letter_agent import (
    build_request,
)


def test_fallback_is_personalized() -> None:
    request = build_request()

    result = build_cover_letter_fallback(request)

    assert result.deterministic_fallback is True

    assert "Backend Engineer" in (result.full_text)

    assert "Example Labs" in (result.full_text)


def test_fallback_uses_only_matched_skills() -> None:
    result = build_cover_letter_fallback(build_request())

    assert "Kubernetes" not in (result.skills_mentioned)

    assert "Python" in (result.skills_mentioned)
