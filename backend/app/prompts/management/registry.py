"""Versioned in-memory prompt registry."""

from __future__ import annotations

from collections.abc import Mapping

from app.prompts.management.models import (
    PromptDefinition,
    parse_prompt_version,
)


class PromptAlreadyRegisteredError(ValueError):
    """Raised for duplicate prompt versions."""


class PromptNotFoundError(KeyError):
    """Raised when a prompt cannot be resolved."""


class PromptRegistry:
    """Stores and resolves versioned prompts."""

    def __init__(self) -> None:
        self._items: dict[
            str,
            dict[str, PromptDefinition],
        ] = {}

    def register(
        self,
        prompt: PromptDefinition,
        *,
        replace: bool = False,
    ) -> None:
        """Register one prompt version."""

        versions = self._items.setdefault(
            prompt.name,
            {},
        )

        if prompt.version in versions and not replace:
            raise PromptAlreadyRegisteredError(
                f"Prompt is already registered: {prompt.name}@{prompt.version}"
            )

        versions[prompt.version] = prompt

    def get(
        self,
        name: str,
        *,
        version: str | None = None,
    ) -> PromptDefinition:
        """Return requested or latest prompt version."""

        versions = self._items.get(name)

        if not versions:
            raise PromptNotFoundError(f"Prompt not found: {name}")

        if version is not None:
            prompt = versions.get(version)

            if prompt is None:
                raise PromptNotFoundError(f"Prompt version not found: {name}@{version}")

            return prompt

        latest_version = max(
            versions,
            key=parse_prompt_version,
        )

        return versions[latest_version]

    def versions(
        self,
        name: str,
    ) -> list[str]:
        """Return versions newest-first."""

        versions = self._items.get(name)

        if not versions:
            raise PromptNotFoundError(f"Prompt not found: {name}")

        return sorted(
            versions,
            key=parse_prompt_version,
            reverse=True,
        )

    def names(self) -> list[str]:
        """Return registered prompt names."""

        return sorted(self._items)

    def latest_prompts(
        self,
    ) -> list[PromptDefinition]:
        """Return latest version of every prompt."""

        return [self.get(name) for name in self.names()]

    def validate_inputs(
        self,
        name: str,
        variables: Mapping[
            str,
            object,
        ],
        *,
        version: str | None = None,
    ) -> list[str]:
        """Return missing prompt variables."""

        prompt = self.get(
            name,
            version=version,
        )

        available = set(variables)

        return sorted(prompt.variables - available)
