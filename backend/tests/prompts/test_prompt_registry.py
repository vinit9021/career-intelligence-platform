"""Tests for versioned Prompt Registry."""

import pytest

from app.prompts.management.models import (
    PromptDefinition,
)
from app.prompts.management.registry import (
    PromptAlreadyRegisteredError,
    PromptNotFoundError,
    PromptRegistry,
)


def make_prompt(
    version: str,
) -> PromptDefinition:
    return PromptDefinition(
        name="resume_parser",
        agent_name="Resume Parser Agent",
        version=version,
        system_prompt=("Parse {resume_text}."),
        user_prompt=("Feedback: {feedback}"),
    )


def test_registry_returns_latest_version() -> None:
    registry = PromptRegistry()

    registry.register(make_prompt("1.0.0"))

    registry.register(make_prompt("1.2.0"))

    registry.register(make_prompt("2.0.0"))

    result = registry.get("resume_parser")

    assert result.version == "2.0.0"


def test_registry_returns_specific_version() -> None:
    registry = PromptRegistry()

    registry.register(make_prompt("1.0.0"))

    registry.register(make_prompt("1.1.0"))

    result = registry.get(
        "resume_parser",
        version="1.0.0",
    )

    assert result.version == "1.0.0"


def test_registry_rejects_duplicate_version() -> None:
    registry = PromptRegistry()

    registry.register(make_prompt("1.0.0"))

    with pytest.raises(PromptAlreadyRegisteredError):
        registry.register(make_prompt("1.0.0"))


def test_registry_reports_missing_variables() -> None:
    registry = PromptRegistry()

    registry.register(make_prompt("1.0.0"))

    missing = registry.validate_inputs(
        "resume_parser",
        {"resume_text": "Resume"},
    )

    assert missing == ["feedback"]


def test_registry_rejects_unknown_prompt() -> None:
    registry = PromptRegistry()

    with pytest.raises(PromptNotFoundError):
        registry.get("unknown_agent")
