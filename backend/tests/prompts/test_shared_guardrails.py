"""Tests for reusable prompt guardrails."""

from app.prompts.management.shared import (
    EVIDENCE_GROUNDING_GUARDRAILS,
    RETRY_GUARDRAILS,
    STRUCTURED_OUTPUT_GUARDRAILS,
    compose_system_prompt,
)


def test_shared_guardrails_are_available() -> None:
    assert "Never invent" in EVIDENCE_GROUNDING_GUARDRAILS

    assert "output schema" in STRUCTURED_OUTPUT_GUARDRAILS

    assert "validation feedback" in RETRY_GUARDRAILS


def test_compose_system_prompt() -> None:
    result = compose_system_prompt(
        "Base instructions.",
        EVIDENCE_GROUNDING_GUARDRAILS,
        RETRY_GUARDRAILS,
    )

    assert result.startswith("Base instructions.")

    assert "Never invent" in result

    assert "validation feedback" in result
