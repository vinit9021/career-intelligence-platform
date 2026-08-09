"""Routing helpers for the central LangGraph workflow."""

from __future__ import annotations

from app.orchestration.state import (
    PIPELINE_ORDER,
    AgentNodeName,
    GraphRoute,
)


def ordered_enabled_nodes(
    enabled_nodes: list[AgentNodeName],
) -> list[AgentNodeName]:
    """Return enabled nodes in canonical order."""

    enabled = set(enabled_nodes)

    return [node for node in PIPELINE_ORDER if node in enabled]


def first_enabled_node(
    enabled_nodes: list[AgentNodeName],
) -> AgentNodeName | None:
    """Return first enabled pipeline node."""

    ordered = ordered_enabled_nodes(enabled_nodes)

    if not ordered:
        return None

    return ordered[0]


def next_enabled_node(
    current: AgentNodeName,
    enabled_nodes: list[AgentNodeName],
) -> AgentNodeName | None:
    """Return next enabled node after current."""

    ordered = ordered_enabled_nodes(enabled_nodes)

    try:
        index = ordered.index(current)

    except ValueError:
        return None

    next_index = index + 1

    if next_index >= len(ordered):
        return None

    return ordered[next_index]


def normalize_route(
    value: GraphRoute | None,
) -> GraphRoute:
    """Convert empty route to finalize."""

    if value is None:
        return "finalize"

    return value
