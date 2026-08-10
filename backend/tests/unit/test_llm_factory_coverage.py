"""Additional coverage for the Groq LLM factory."""

from __future__ import annotations

from typing import Any, cast

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

import app.llm.factory as factory
from app.agents.base.errors import AgentConfigurationError


def test_required_environment_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "COVERAGE_VALUE",
        "  configured  ",
    )

    assert factory._required_environment_value("COVERAGE_VALUE") == "configured"


def test_required_environment_value_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "COVERAGE_VALUE",
        "   ",
    )

    with pytest.raises(
        AgentConfigurationError,
        match="COVERAGE_VALUE",
    ):
        factory._required_environment_value("COVERAGE_VALUE")


def test_positive_integer_uses_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "COVERAGE_INTEGER",
        raising=False,
    )

    assert (
        factory._positive_integer_environment_value(
            "COVERAGE_INTEGER",
            7,
        )
        == 7
    )


@pytest.mark.parametrize(
    "value",
    [
        "wrong",
        "0",
        "-3",
    ],
)
def test_positive_integer_rejects_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    monkeypatch.setenv(
        "COVERAGE_INTEGER",
        value,
    )

    with pytest.raises(AgentConfigurationError):
        factory._positive_integer_environment_value(
            "COVERAGE_INTEGER",
            2,
        )


def test_create_chat_model_rejects_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "openai",
    )

    with pytest.raises(
        AgentConfigurationError,
        match="Unsupported LLM provider",
    ):
        factory.create_chat_model()


def test_create_chat_model_requires_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "groq",
    )

    monkeypatch.setenv(
        "GROQ_API_KEY",
        "",
    )

    with pytest.raises(
        AgentConfigurationError,
        match="GROQ_API_KEY",
    ):
        factory.create_chat_model()


def test_create_chat_model_requires_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "groq",
    )

    monkeypatch.setenv(
        "GROQ_API_KEY",
        "test-key",
    )

    monkeypatch.setenv(
        "GROQ_MODEL",
        "",
    )

    with pytest.raises(
        AgentConfigurationError,
        match="GROQ_MODEL",
    ):
        factory.create_chat_model()


def test_create_chat_model_builds_groq(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "LLM_PROVIDER",
        "groq",
    )

    monkeypatch.setenv(
        "GROQ_API_KEY",
        "test-key",
    )

    monkeypatch.setenv(
        "GROQ_MODEL",
        "test-model",
    )

    monkeypatch.setenv(
        "AGENT_TIMEOUT_SECONDS",
        "45",
    )

    monkeypatch.setenv(
        "AGENT_MODEL_MAX_RETRIES",
        "4",
    )

    captured: dict[str, Any] = {}

    sentinel = cast(
        BaseChatModel,
        object(),
    )

    def fake_chat_groq(
        **kwargs: Any,
    ) -> BaseChatModel:
        captured.update(kwargs)

        return sentinel

    monkeypatch.setattr(
        factory,
        "ChatGroq",
        fake_chat_groq,
    )

    result = factory.create_chat_model()

    assert result is sentinel

    assert captured == {
        "model": "test-model",
        "temperature": 0,
        "timeout": 45,
        "max_retries": 4,
    }
