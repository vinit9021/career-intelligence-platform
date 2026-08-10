"""Models used by prompt management."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

_VARIABLE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def extract_prompt_variables(
    value: str,
) -> set[str]:
    """Return template variables used by a prompt."""

    return set(_VARIABLE_PATTERN.findall(value))


def parse_prompt_version(
    version: str,
) -> tuple[int, int, int]:
    """Convert semantic prompt version to sortable tuple."""

    if not _VERSION_PATTERN.fullmatch(version):
        raise ValueError("Prompt version must use MAJOR.MINOR.PATCH format.")

    major, minor, patch = version.split(".")

    return (
        int(major),
        int(minor),
        int(patch),
    )


class PromptDefinition(BaseModel):
    """Versioned prompt definition."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9_]+$",
    )

    agent_name: str = Field(min_length=1)

    version: str

    system_prompt: str = Field(min_length=1)

    user_prompt: str = Field(min_length=1)

    description: str = ""

    tags: list[str] = Field(default_factory=list)

    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("version")
    @classmethod
    def validate_version(
        cls,
        value: str,
    ) -> str:
        parse_prompt_version(value)

        return value

    @property
    def variables(self) -> set[str]:
        """Variables required by both prompts."""

        return extract_prompt_variables(self.system_prompt) | extract_prompt_variables(
            self.user_prompt
        )

    @property
    def checksum(self) -> str:
        """Stable checksum for prompt auditing."""

        value = self.system_prompt + "\n---USER---\n" + self.user_prompt

        return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PromptModuleSpec:
    """Maps one agent to its existing prompt module."""

    name: str
    agent_name: str
    module_name: str
    version: str = "1.0.0"
    description: str = ""
