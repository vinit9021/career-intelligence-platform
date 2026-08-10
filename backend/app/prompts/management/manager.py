"""High-level prompt management API."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.prompts import (
    ChatPromptTemplate,
)

from app.prompts.management.catalog import (
    build_default_prompt_registry,
)
from app.prompts.management.models import (
    PromptDefinition,
)
from app.prompts.management.registry import (
    PromptRegistry,
)


class PromptManager:
    """Resolves and validates versioned agent prompts."""

    def __init__(
        self,
        registry: PromptRegistry,
        *,
        version_overrides: (dict[str, str] | None) = None,
    ) -> None:
        self.registry = registry

        self.version_overrides = dict(version_overrides or {})

    def resolve(
        self,
        name: str,
        *,
        version: str | None = None,
    ) -> PromptDefinition:
        """Resolve configured prompt version."""

        selected_version = version if version is not None else self.version_overrides.get(name)

        return self.registry.get(
            name,
            version=selected_version,
        )

    def validate_variables(
        self,
        name: str,
        variables: dict[
            str,
            Any,
        ],
        *,
        version: str | None = None,
    ) -> list[str]:
        """Return missing variables."""

        prompt = self.resolve(
            name,
            version=version,
        )

        return sorted(prompt.variables - set(variables))

    def build_chat_prompt(
        self,
        name: str,
        *,
        version: str | None = None,
    ) -> ChatPromptTemplate:
        """Create LangChain chat prompt."""

        prompt = self.resolve(
            name,
            version=version,
        )

        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    prompt.system_prompt,
                ),
                (
                    "human",
                    prompt.user_prompt,
                ),
            ]
        )


@lru_cache(maxsize=1)
def get_default_prompt_manager() -> PromptManager:
    """Return cached application prompt manager."""

    return PromptManager(build_default_prompt_registry())


def build_chat_prompt(
    name: str,
    *,
    version: str | None = None,
) -> ChatPromptTemplate:
    """Convenience API used by agents."""

    return get_default_prompt_manager().build_chat_prompt(
        name,
        version=version,
    )
