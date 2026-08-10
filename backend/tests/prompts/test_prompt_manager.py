"""Tests for Prompt Manager."""

from app.prompts.management.manager import (
    PromptManager,
)
from app.prompts.management.models import (
    PromptDefinition,
)
from app.prompts.management.registry import (
    PromptRegistry,
)


def build_registry() -> PromptRegistry:
    registry = PromptRegistry()

    registry.register(
        PromptDefinition(
            name="test_agent",
            agent_name="Test Agent",
            version="1.0.0",
            system_prompt=("System {context}"),
            user_prompt=("Input {message}"),
        )
    )

    registry.register(
        PromptDefinition(
            name="test_agent",
            agent_name="Test Agent",
            version="2.0.0",
            system_prompt=("System v2 {context}"),
            user_prompt=("Input v2 {message}"),
        )
    )

    return registry


def test_manager_uses_latest_by_default() -> None:
    manager = PromptManager(build_registry())

    prompt = manager.resolve("test_agent")

    assert prompt.version == "2.0.0"


def test_manager_supports_version_override() -> None:
    manager = PromptManager(
        build_registry(),
        version_overrides={"test_agent": "1.0.0"},
    )

    prompt = manager.resolve("test_agent")

    assert prompt.version == "1.0.0"


def test_manager_builds_langchain_prompt() -> None:
    manager = PromptManager(build_registry())

    chat_prompt = manager.build_chat_prompt("test_agent")

    assert "context" in chat_prompt.input_variables

    assert "message" in chat_prompt.input_variables
