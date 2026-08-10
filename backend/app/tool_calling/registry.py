"""Central registry for tools available to AI agents."""

from __future__ import annotations

from collections.abc import (
    Awaitable,
    Callable,
)
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

ToolHandler = Callable[
    [dict[str, Any]],
    Awaitable[Any],
]


class ToolAlreadyRegisteredError(ValueError):
    """Raised when the same tool is registered twice."""


class ToolNotFoundError(KeyError):
    """Raised when a requested tool is unknown."""


@dataclass(frozen=True)
class ToolDefinition:
    """Definition of one callable agent tool."""

    name: str

    description: str

    args_schema: type[BaseModel]

    handler: ToolHandler

    timeout_seconds: float = 30.0

    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Tool name cannot be empty.")

        if not self.description:
            raise ValueError("Tool description cannot be empty.")

        if self.timeout_seconds <= 0:
            raise ValueError("Tool timeout must be positive.")


class ToolRegistry:
    """Stores callable tools by unique name."""

    def __init__(self) -> None:
        self._tools: dict[
            str,
            ToolDefinition,
        ] = {}

    def register(
        self,
        definition: ToolDefinition,
        *,
        replace: bool = False,
    ) -> None:
        """Register one tool."""

        if definition.name in self._tools and not replace:
            raise ToolAlreadyRegisteredError(f"Tool already registered: {definition.name}")

        self._tools[definition.name] = definition

    def get(
        self,
        name: str,
    ) -> ToolDefinition:
        """Return one registered tool."""

        definition = self._tools.get(name)

        if definition is None:
            raise ToolNotFoundError(f"Tool not found: {name}")

        return definition

    def contains(
        self,
        name: str,
    ) -> bool:
        """Whether a tool is registered."""

        return name in self._tools

    def names(self) -> list[str]:
        """Return registered tool names."""

        return sorted(self._tools)

    def definitions(
        self,
    ) -> list[ToolDefinition]:
        """Return all registered tools."""

        return [self._tools[name] for name in self.names()]
