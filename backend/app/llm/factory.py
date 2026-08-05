"""Provider-independent language-model factory."""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq

from app.agents.base.errors import AgentConfigurationError


def _required_environment_value(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        raise AgentConfigurationError(
            f"{name} must be configured before a live AI agent can run."
        )

    return value


def _positive_integer_environment_value(
    name: str,
    default: int,
) -> int:
    raw_value = os.getenv(name, str(default)).strip()

    try:
        parsed_value = int(raw_value)
    except ValueError as exc:
        raise AgentConfigurationError(
            f"{name} must be a valid integer."
        ) from exc

    if parsed_value < 1:
        raise AgentConfigurationError(
            f"{name} must be greater than zero."
        )

    return parsed_value


def create_chat_model() -> BaseChatModel:
    """Create the Groq chat model used by platform agents."""

    provider = os.getenv(
        "LLM_PROVIDER",
        "groq",
    ).strip().casefold()

    if provider != "groq":
        raise AgentConfigurationError(
            f"Unsupported LLM provider: {provider!r}. "
            "This project is currently configured for Groq."
        )

    _required_environment_value("GROQ_API_KEY")
    model_name = _required_environment_value("GROQ_MODEL")

    timeout_seconds = _positive_integer_environment_value(
        "AGENT_TIMEOUT_SECONDS",
        60,
    )

    maximum_retries = _positive_integer_environment_value(
        "AGENT_MODEL_MAX_RETRIES",
        2,
    )

    return ChatGroq(
        model=model_name,
        temperature=0,
        timeout=timeout_seconds,
        max_retries=maximum_retries,
    )
