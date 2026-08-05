"""LangGraph ATS Optimization Agent workflow."""

from __future__ import annotations

from typing import Any, Literal, cast
from uuid import uuid4

from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.ats_optimization.agent import (
    ATSOptimizationRunnable,
    build_ats_optimization_runnable,
)
from app.agents.ats_optimization.state import (
    ATSOptimizationAgentInput,
    ATSOptimizationAnalysis,
    ATSOptimizationBaseline,
    ATSOptimizationRequest,
    ATSOptimizationResult,
    ATSOptimizationState,
    ATSOptimizationWorkflowResult,
)
from app.agents.ats_optimization.validator import (
    validate_ats_optimization_output,
)
from app.agents.base.errors import (
    AgentConfigurationError,
    AgentExecutionError,
)
from app.ats.optimizer import (
    build_ats_baseline,
    build_ats_fallback_result,
)
from app.llm.factory import create_chat_model

_AGENT_NAME = "groq_ats_optimization_agent"
_AGENT_VERSION = "1.0.0"


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _merge_optimization_result(
    baseline: ATSOptimizationBaseline,
    analysis: ATSOptimizationAnalysis,
    validator_warnings: list[str],
) -> ATSOptimizationResult:
    safe_keywords = _deduplicate(
        [item.keyword for item in analysis.keyword_recommendations if item.safe_to_add]
    )

    conditional_keywords = _deduplicate(
        [item.keyword for item in analysis.keyword_recommendations if not item.safe_to_add]
    )

    supported_change_count = (
        len(safe_keywords)
        + len(analysis.bullet_rewrites)
        + (1 if analysis.summary_rewrite is not None else 0)
    )

    maximum_supported_gain = min(
        25.0,
        float(supported_change_count * 3),
    )

    projected_score = min(
        100.0,
        baseline.baseline_score + maximum_supported_gain,
        max(
            baseline.baseline_score,
            analysis.proposed_ats_score,
        ),
    )

    projected_score = round(
        projected_score,
        2,
    )

    score_gain = round(
        projected_score - baseline.baseline_score,
        2,
    )

    actions = _deduplicate(
        [
            *analysis.prioritized_actions,
            *baseline.deterministic_actions,
        ]
    )

    warnings = _deduplicate(
        [
            *baseline.warnings,
            *analysis.warnings,
            *validator_warnings,
        ]
    )

    return ATSOptimizationResult(
        baseline_score=baseline.baseline_score,
        projected_ats_score=projected_score,
        projected_score_gain=score_gain,
        keyword_coverage_score=(baseline.keyword_coverage_score),
        section_completeness_score=(baseline.section_completeness_score),
        existing_keywords=list(baseline.existing_keywords),
        missing_high_priority_keywords=list(baseline.missing_high_priority_keywords),
        missing_preferred_keywords=list(baseline.missing_preferred_keywords),
        safe_keywords_to_add=safe_keywords,
        conditional_keywords=conditional_keywords,
        summary_rewrite=analysis.summary_rewrite,
        bullet_rewrites=list(analysis.bullet_rewrites),
        section_recommendations=list(analysis.section_recommendations),
        prioritized_actions=actions,
        warnings=warnings,
        agent_name=_AGENT_NAME,
        agent_version=_AGENT_VERSION,
        deterministic_fallback=False,
    )


def _build_unavailable_runnable(
    message: str,
) -> ATSOptimizationRunnable:
    async def unavailable_model(
        _: dict[str, Any],
    ) -> ATSOptimizationAnalysis:
        raise AgentConfigurationError(message)

    return cast(
        ATSOptimizationRunnable,
        RunnableLambda(unavailable_model),
    )


def _create_default_runnable() -> ATSOptimizationRunnable:
    try:
        model = create_chat_model()
    except AgentConfigurationError as exc:
        return _build_unavailable_runnable(str(exc))

    return build_ats_optimization_runnable(model)


def build_ats_optimization_workflow(
    runnable: ATSOptimizationRunnable,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Build the retryable ATS workflow."""

    async def create_baseline(
        state: ATSOptimizationState,
    ) -> dict[str, Any]:
        try:
            baseline = build_ats_baseline(state["request"])

            return {
                "baseline": baseline,
                "status": "analyzing",
                "last_error": None,
            }
        except Exception as exc:
            return {
                "baseline": None,
                "status": "failed",
                "last_error": (f"Deterministic ATS baseline failed: {exc}"),
            }

    async def analyze(
        state: ATSOptimizationState,
    ) -> dict[str, Any]:
        baseline = state.get("baseline")

        if baseline is None:
            return {
                "status": "failed",
                "last_error": ("ATS baseline is unavailable."),
            }

        attempt_count = (
            state.get(
                "attempt_count",
                0,
            )
            + 1
        )

        agent_input = ATSOptimizationAgentInput(
            request=state["request"],
            baseline=baseline,
            validation_feedback=state.get(
                "validation_errors",
                [],
            ),
        )

        try:
            output = await runnable.ainvoke(agent_input.to_prompt_payload())

            return {
                "agent_result": output,
                "attempt_count": attempt_count,
                "status": "validating",
                "last_error": None,
            }
        except Exception as exc:
            return {
                "agent_result": None,
                "attempt_count": attempt_count,
                "validation_errors": [f"Agent invocation failed: {exc}"],
                "status": "retrying",
                "last_error": str(exc),
            }

    async def validate(
        state: ATSOptimizationState,
    ) -> dict[str, Any]:
        analysis = state.get("agent_result")
        baseline = state.get("baseline")

        attempt_count = state.get(
            "attempt_count",
            0,
        )

        max_attempts = state.get(
            "max_attempts",
            2,
        )

        if analysis is None:
            return {"status": ("retrying" if attempt_count < max_attempts else "failed")}

        validation = validate_ats_optimization_output(
            state["request"],
            analysis,
        )

        combined_warnings = _deduplicate(
            [
                *state.get("warnings", []),
                *validation.warnings,
            ]
        )

        if validation.is_valid and baseline is not None:
            final_result = _merge_optimization_result(
                baseline,
                analysis,
                combined_warnings,
            )

            return {
                "final_result": final_result,
                "validation_errors": [],
                "warnings": combined_warnings,
                "status": "completed",
                "last_error": None,
            }

        return {
            "validation_errors": validation.errors,
            "warnings": combined_warnings,
            "status": ("retrying" if attempt_count < max_attempts else "failed"),
        }

    async def fallback(
        state: ATSOptimizationState,
    ) -> dict[str, Any]:
        baseline = state.get("baseline")

        if baseline is None:
            return {
                "final_result": None,
                "status": "failed",
                "last_error": ("AI optimization and deterministic ATS analysis both failed."),
            }

        result = build_ats_fallback_result(baseline)

        return {
            "final_result": result,
            "warnings": list(result.warnings),
            "status": "completed_with_fallback",
        }

    async def reject(
        state: ATSOptimizationState,
    ) -> dict[str, Any]:
        return {
            "status": "failed",
            "last_error": state.get("last_error"),
        }

    async def finalize(
        state: ATSOptimizationState,
    ) -> dict[str, Any]:
        return {
            "status": state.get(
                "status",
                "completed",
            )
        }

    def route_after_baseline(
        state: ATSOptimizationState,
    ) -> Literal["analyze", "reject"]:
        if state.get("status") == "failed" or state.get("baseline") is None:
            return "reject"

        return "analyze"

    def route_after_validation(
        state: ATSOptimizationState,
    ) -> Literal[
        "analyze",
        "finalize",
        "fallback",
    ]:
        if state.get("status") == "completed":
            return "finalize"

        if state.get("status") == "retrying" and state.get("attempt_count", 0) < state.get(
            "max_attempts", 2
        ):
            return "analyze"

        return "fallback"

    builder = StateGraph(ATSOptimizationState)

    builder.add_node(
        "baseline",
        RunnableLambda(create_baseline),
    )

    builder.add_node(
        "analyze",
        RunnableLambda(analyze),
    )

    builder.add_node(
        "validate",
        RunnableLambda(validate),
    )

    builder.add_node(
        "fallback",
        RunnableLambda(fallback),
    )

    builder.add_node(
        "reject",
        RunnableLambda(reject),
    )

    builder.add_node(
        "finalize",
        RunnableLambda(finalize),
    )

    builder.add_edge(
        START,
        "baseline",
    )

    builder.add_conditional_edges(
        "baseline",
        route_after_baseline,
        {
            "analyze": "analyze",
            "reject": "reject",
        },
    )

    builder.add_edge(
        "analyze",
        "validate",
    )

    builder.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "analyze": "analyze",
            "finalize": "finalize",
            "fallback": "fallback",
        },
    )

    builder.add_edge(
        "finalize",
        END,
    )

    builder.add_edge(
        "fallback",
        END,
    )

    builder.add_edge(
        "reject",
        END,
    )

    if use_checkpointer:
        return builder.compile(checkpointer=InMemorySaver())

    return builder.compile()


async def run_ats_optimization_workflow(
    *,
    request: ATSOptimizationRequest,
    runnable: ATSOptimizationRunnable | None = None,
    max_attempts: int = 2,
    thread_id: str | None = None,
) -> ATSOptimizationWorkflowResult:
    """Execute the ATS Optimization workflow."""

    selected_runnable = runnable if runnable is not None else _create_default_runnable()

    graph = build_ats_optimization_workflow(selected_runnable)

    initial_state: ATSOptimizationState = {
        "request": request,
        "baseline": None,
        "agent_result": None,
        "final_result": None,
        "attempt_count": 0,
        "max_attempts": max_attempts,
        "validation_errors": [],
        "warnings": [],
        "status": "pending",
        "last_error": None,
    }

    configuration = {
        "configurable": {"thread_id": (thread_id if thread_id is not None else str(uuid4()))}
    }

    raw_result = await graph.ainvoke(
        initial_state,
        config=configuration,
    )

    if not isinstance(raw_result, dict):
        raise AgentExecutionError("ATS Optimization Agent returned invalid workflow state.")

    return ATSOptimizationWorkflowResult(
        status=raw_result.get(
            "status",
            "failed",
        ),
        optimization_result=raw_result.get("final_result"),
        agent_analysis=raw_result.get("agent_result"),
        attempt_count=raw_result.get(
            "attempt_count",
            0,
        ),
        warnings=raw_result.get(
            "warnings",
            [],
        ),
        validation_errors=raw_result.get(
            "validation_errors",
            [],
        ),
        last_error=raw_result.get("last_error"),
    )
