"""Permission policy for agent tool access."""

from __future__ import annotations

from collections.abc import (
    Collection,
    Mapping,
)


class ToolPermissionPolicy:
    """Controls which tools each agent may invoke."""

    def __init__(
        self,
        permissions: (
            Mapping[
                str,
                Collection[str],
            ]
            | None
        ) = None,
    ) -> None:
        self._permissions: dict[
            str,
            frozenset[str],
        ] = {agent: frozenset(tools) for agent, tools in (permissions or {}).items()}

    def is_allowed(
        self,
        *,
        agent_name: str,
        tool_name: str,
    ) -> bool:
        """Check whether an agent may call a tool."""

        allowed = self._permissions.get(
            agent_name,
            frozenset(),
        )

        return "*" in allowed or tool_name in allowed

    def allowed_tools(
        self,
        agent_name: str,
    ) -> set[str]:
        """Return configured tools for an agent."""

        return set(
            self._permissions.get(
                agent_name,
                frozenset(),
            )
        )

    def grant(
        self,
        *,
        agent_name: str,
        tool_name: str,
    ) -> None:
        """Grant a tool permission."""

        current = set(
            self._permissions.get(
                agent_name,
                frozenset(),
            )
        )

        current.add(tool_name)

        self._permissions[agent_name] = frozenset(current)

    def revoke(
        self,
        *,
        agent_name: str,
        tool_name: str,
    ) -> None:
        """Remove a tool permission."""

        current = set(
            self._permissions.get(
                agent_name,
                frozenset(),
            )
        )

        current.discard(tool_name)

        self._permissions[agent_name] = frozenset(current)
