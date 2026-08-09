"""Registry for central workflow agent executors."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.orchestration.state import (
    AgentNodeName,
    AgentNodeResult,
    CareerWorkflowState,
)

AgentExecutor = Callable[
    [CareerWorkflowState],
    Awaitable[AgentNodeResult],
]


@dataclass(frozen=True)
class AgentRegistration:
    """Primary and fallback executors for one node."""

    executor: AgentExecutor

    fallback: AgentExecutor | None = None


class AgentRegistry:
    """Registry of independently implemented agents."""

    def __init__(self) -> None:
        self._agents: dict[
            AgentNodeName,
            AgentRegistration,
        ] = {}

    def register(
        self,
        name: AgentNodeName,
        executor: AgentExecutor,
        *,
        fallback: AgentExecutor | None = None,
    ) -> None:
        """Register or replace an agent executor."""

        self._agents[name] = AgentRegistration(
            executor=executor,
            fallback=fallback,
        )

    def get(
        self,
        name: AgentNodeName,
    ) -> AgentRegistration:
        """Return registration for one node."""

        registration = self._agents.get(name)

        if registration is None:
            raise KeyError(f"Agent node is not registered: {name}")

        return registration

    def contains(
        self,
        name: AgentNodeName,
    ) -> bool:
        """Check whether a node is registered."""

        return name in self._agents

    def validate_nodes(
        self,
        nodes: list[AgentNodeName],
    ) -> list[str]:
        """Return errors for missing registrations."""

        return [
            (f"Agent node is enabled but not registered: {name}")
            for name in nodes
            if name not in self._agents
        ]
