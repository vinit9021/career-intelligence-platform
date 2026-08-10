"""Tests for prompt models."""

import pytest
from pydantic import ValidationError

from app.prompts.management.models import (
    PromptDefinition,
    extract_prompt_variables,
)


def build_prompt(
    *,
    version: str = "1.0.0",
) -> PromptDefinition:
    return PromptDefinition(
        name="test_agent",
        agent_name="Test Agent",
        version=version,
        system_prompt=("Analyze {resume}."),
        user_prompt=("Role: {job_description}"),
    )


def test_extracts_prompt_variables() -> None:
    variables = extract_prompt_variables("Hello {name}. Analyze {resume}.")

    assert variables == {
        "name",
        "resume",
    }


def test_definition_combines_variables() -> None:
    prompt = build_prompt()

    assert prompt.variables == {
        "resume",
        "job_description",
    }


def test_checksum_is_stable() -> None:
    first = build_prompt()
    second = build_prompt()

    assert first.checksum == second.checksum


def test_rejects_invalid_version() -> None:
    with pytest.raises(ValidationError):
        build_prompt(version="v1")
