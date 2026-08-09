"""Central LangGraph workflow for career intelligence."""

from __future__ import annotations

from collections.abc import Hashable
from typing import Any, cast
from uuid import uuid4

from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.orchestration.registry import (
    AgentRegistry,
)
from app.orchestration.router import (
    first_enabled_node,
    next_enabled_node,
    normalize_route,
)
from app.orchestration.state import (
    PIPELINE_ORDER,
    AgentNodeName,
    AgentNodeResult,
    CareerWorkflowRequest,
    CareerWorkflowResult,
    CareerWorkflowState,
    GraphRoute,
)


def _deduplicate(
    values: list[str],
) -> list[str]:
    return list(dict.fromkeys(values))


def _route_map() -> dict[Hashable, str]:
    routes: dict[Hashable, str] = {node: node for node in PIPELINE_ORDER}

    routes["fallback"] = "fallback"
    routes["finalize"] = "finalize"

    return routes


def _route_state(
    state: CareerWorkflowState,
) -> GraphRoute:
    if state.get("status") == "failed":
        return "finalize"

    return normalize_route(state.get("next_node"))


def _store_success(
    state: CareerWorkflowState,
    *,
    node: AgentNodeName,
    result: AgentNodeResult,
    fallback_used: bool,
) -> dict[str, Any]:
    outputs = dict(
        state.get(
            "outputs",
            {},
        )
    )

    outputs[node] = result.output

    execution_order = [
        *state.get(
            "execution_order",
            [],
        ),
        node,
    ]

    fallback_nodes = list(
        state.get(
            "fallback_nodes",
            [],
        )
    )

    if fallback_used:
        fallback_nodes.append(node)

    warnings = _deduplicate(
        [
            *state.get(
                "warnings",
                [],
            ),
            *result.warnings,
        ]
    )

    request = state["request"]

    next_node = next_enabled_node(
        node,
        request.enabled_nodes,
    )

    return {
        "outputs": outputs,
        "execution_order": execution_order,
        "fallback_nodes": fallback_nodes,
        "warnings": warnings,
        "current_node": node,
        "failed_node": None,
        "next_node": next_node,
        "status": "running",
        "last_error": None,
    }


def _build_agent_node(
    *,
    name: AgentNodeName,
    registry: AgentRegistry,
) -> Any:
    async def execute(
        state: CareerWorkflowState,
    ) -> dict[str, Any]:
        registration = registry.get(name)

        try:
            result = await registration.executor(state)

        except Exception as exc:
            result = AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=True,
            )

        if result.status == "completed":
            return _store_success(
                state,
                node=name,
                result=result,
                fallback_used=False,
            )

        message = result.error or (f"Agent node failed without an error message: {name}")

        warnings = _deduplicate(
            [
                *state.get(
                    "warnings",
                    [],
                ),
                *result.warnings,
            ]
        )

        retry_counts = dict(
            state.get(
                "retry_counts",
                {},
            )
        )

        retries_used = retry_counts.get(
            name,
            0,
        )

        max_retries = state.get(
            "max_retries",
            1,
        )

        if result.retryable and retries_used < max_retries:
            retry_counts[name] = retries_used + 1

            return {
                "retry_counts": retry_counts,
                "warnings": warnings,
                "current_node": name,
                "failed_node": name,
                "next_node": name,
                "status": "running",
                "last_error": message,
            }

        if registration.fallback is not None:
            return {
                "retry_counts": retry_counts,
                "warnings": warnings,
                "current_node": name,
                "failed_node": name,
                "next_node": "fallback",
                "status": "running",
                "last_error": message,
            }

        errors = _deduplicate(
            [
                *state.get(
                    "errors",
                    [],
                ),
                message,
            ]
        )

        return {
            "errors": errors,
            "warnings": warnings,
            "current_node": name,
            "failed_node": name,
            "next_node": "finalize",
            "status": "failed",
            "last_error": message,
        }

    return RunnableLambda(execute)


def build_career_workflow(
    registry: AgentRegistry,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Build the central multi-agent LangGraph."""

    async def initialize(
        state: CareerWorkflowState,
    ) -> dict[str, Any]:
        request = state["request"]

        errors = registry.validate_nodes(request.enabled_nodes)

        if errors:
            return {
                "status": "failed",
                "errors": errors,
                "last_error": errors[0],
                "next_node": "finalize",
            }

        next_node = first_enabled_node(request.enabled_nodes)

        return {
            "context": dict(request.initial_context),
            "outputs": {},
            "execution_order": [],
            "fallback_nodes": [],
            "retry_counts": {},
            "warnings": [],
            "errors": [],
            "current_node": None,
            "failed_node": None,
            "next_node": next_node,
            "status": "running",
            "last_error": None,
        }

    async def fallback(
        state: CareerWorkflowState,
    ) -> dict[str, Any]:
        failed_node = state.get("failed_node")

        if failed_node is None:
            message = "Fallback requested without a failed agent node."

            return {
                "status": "failed",
                "errors": _deduplicate(
                    [
                        *state.get(
                            "errors",
                            [],
                        ),
                        message,
                    ]
                ),
                "next_node": "finalize",
                "last_error": message,
            }

        registration = registry.get(failed_node)

        fallback_executor = registration.fallback

        if fallback_executor is None:
            message = f"No fallback executor registered for node: {failed_node}"

            return {
                "status": "failed",
                "errors": _deduplicate(
                    [
                        *state.get(
                            "errors",
                            [],
                        ),
                        message,
                    ]
                ),
                "next_node": "finalize",
                "last_error": message,
            }

        try:
            result = await fallback_executor(state)

        except Exception as exc:
            result = AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=False,
            )

        if result.status == "completed":
            return _store_success(
                state,
                node=failed_node,
                result=result,
                fallback_used=True,
            )

        message = result.error or (f"Fallback executor failed for node: {failed_node}")

        return {
            "status": "failed",
            "errors": _deduplicate(
                [
                    *state.get(
                        "errors",
                        [],
                    ),
                    message,
                ]
            ),
            "warnings": _deduplicate(
                [
                    *state.get(
                        "warnings",
                        [],
                    ),
                    *result.warnings,
                ]
            ),
            "next_node": "finalize",
            "last_error": message,
        }

    async def finalize(
        state: CareerWorkflowState,
    ) -> dict[str, Any]:
        if state.get("status") == "failed":
            return {
                "status": "failed",
                "next_node": None,
            }

        return {
            "status": "completed",
            "next_node": None,
            "last_error": None,
        }

    builder = StateGraph(CareerWorkflowState)

    builder.add_node(
        "initialize",
        cast(
            Any,
            RunnableLambda(initialize),
        ),
    )

    for name in PIPELINE_ORDER:
        builder.add_node(
            name,
            cast(
                Any,
                _build_agent_node(
                    name=name,
                    registry=registry,
                ),
            ),
        )

    builder.add_node(
        "fallback",
        cast(
            Any,
            RunnableLambda(fallback),
        ),
    )

    builder.add_node(
        "finalize",
        cast(
            Any,
            RunnableLambda(finalize),
        ),
    )

    builder.add_edge(
        START,
        "initialize",
    )

    routes = _route_map()

    builder.add_conditional_edges(
        "initialize",
        _route_state,
        routes,
    )

    for name in PIPELINE_ORDER:
        builder.add_conditional_edges(
            name,
            _route_state,
            routes,
        )

    builder.add_conditional_edges(
        "fallback",
        _route_state,
        routes,
    )

    builder.add_edge(
        "finalize",
        END,
    )

    if use_checkpointer:
        return builder.compile(checkpointer=InMemorySaver())

    return builder.compile()


async def run_career_workflow(
    *,
    registry: AgentRegistry,
    request: CareerWorkflowRequest,
    max_retries: int = 1,
    thread_id: str | None = None,
) -> CareerWorkflowResult:
    """Execute central multi-agent workflow."""

    graph = build_career_workflow(registry)

    initial_state: CareerWorkflowState = {
        "request": request,
        "context": dict(request.initial_context),
        "outputs": {},
        "execution_order": [],
        "fallback_nodes": [],
        "retry_counts": {},
        "max_retries": max_retries,
        "current_node": None,
        "failed_node": None,
        "next_node": None,
        "status": "pending",
        "warnings": [],
        "errors": [],
        "last_error": None,
    }

    raw_result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": (thread_id or str(uuid4()))}},
    )

    return CareerWorkflowResult(
        status=raw_result.get(
            "status",
            "failed",
        ),
        outputs=raw_result.get(
            "outputs",
            {},
        ),
        execution_order=raw_result.get(
            "execution_order",
            [],
        ),
        fallback_nodes=raw_result.get(
            "fallback_nodes",
            [],
        ),
        retry_counts=raw_result.get(
            "retry_counts",
            {},
        ),
        warnings=raw_result.get(
            "warnings",
            [],
        ),
        errors=raw_result.get(
            "errors",
            [],
        ),
        failed_node=raw_result.get("failed_node"),
        last_error=raw_result.get("last_error"),
    )
