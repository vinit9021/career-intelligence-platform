"""LangGraph workflow for Skill Gap AI Agent."""

from __future__ import annotations

from typing import Any, Literal, cast
from uuid import uuid4

from langchain_core.runnables import (
    RunnableLambda,
)
from langgraph.checkpoint.memory import (
    InMemorySaver,
)
from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from app.agents.base.errors import (
    AgentConfigurationError,
)
from app.agents.skill_gap.agent import (
    SkillGapRunnable,
    build_skill_gap_runnable,
)
from app.agents.skill_gap.state import (
    SkillGapAgentInput,
    SkillGapAnalysis,
    SkillGapRequest,
    SkillGapResult,
    SkillGapState,
    SkillGapWorkflowResult,
)
from app.agents.skill_gap.validator import (
    validate_skill_gap_output,
)
from app.llm.factory import create_chat_model
from app.skill_gap.analyzer import (
    build_skill_gap_baseline,
    build_skill_gap_fallback,
)


def _deduplicate(
    values: list[str],
) -> list[str]:
    return list(dict.fromkeys(values))


def _build_unavailable_runnable(
    message: str,
) -> SkillGapRunnable:
    async def unavailable(
        _: dict[str, Any],
    ) -> SkillGapAnalysis:
        raise AgentConfigurationError(message)

    return cast(
        SkillGapRunnable,
        RunnableLambda(unavailable),
    )


def _create_default_runnable() -> SkillGapRunnable:
    try:
        model = create_chat_model()

    except AgentConfigurationError as exc:
        return _build_unavailable_runnable(str(exc))

    return build_skill_gap_runnable(model)


def _merge_result(
    state: SkillGapState,
) -> SkillGapResult:
    request = state["request"]

    baseline = state["baseline"]

    analysis = state["agent_result"]

    if baseline is None or analysis is None:
        raise ValueError("Cannot merge incomplete Skill Gap state.")

    by_skill = {gap.skill.casefold(): gap for gap in analysis.gaps}

    merged_gaps = []

    for deterministic_gap in baseline.deterministic_gaps:
        merged_gaps.append(
            by_skill.get(
                deterministic_gap.skill.casefold(),
                deterministic_gap,
            )
        )

    allowed_skills = {gap.skill.casefold() for gap in merged_gaps}

    roadmap = [
        step
        for step in analysis.learning_roadmap
        if (step.target_skill.casefold() in allowed_skills)
    ][: request.max_roadmap_steps]

    projects = [
        project
        for project in analysis.mini_projects
        if all(skill.casefold() in allowed_skills for skill in project.target_skills)
    ][: request.max_mini_projects]

    return SkillGapResult(
        gap_score=baseline.gap_score,
        matched_skills=(baseline.matched_skills),
        gaps=merged_gaps,
        learning_roadmap=roadmap,
        mini_projects=projects,
        summary=analysis.summary,
        warnings=_deduplicate(
            [
                *baseline.warnings,
                *analysis.warnings,
                *state.get(
                    "warnings",
                    [],
                ),
            ]
        ),
        deterministic_fallback=False,
    )


def build_skill_gap_workflow(
    runnable: SkillGapRunnable,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Build retryable Skill Gap workflow."""

    async def baseline_node(
        state: SkillGapState,
    ) -> dict[str, Any]:
        try:
            baseline = build_skill_gap_baseline(state["request"])

            return {
                "baseline": baseline,
                "status": "analyzing",
                "last_error": None,
            }

        except Exception as exc:
            return {
                "baseline": None,
                "status": "failed",
                "last_error": str(exc),
            }

    async def analyze_node(
        state: SkillGapState,
    ) -> dict[str, Any]:
        baseline = state.get("baseline")

        if baseline is None:
            return {
                "status": "failed",
                "last_error": ("Skill-gap baseline is unavailable."),
            }

        attempt_count = (
            state.get(
                "attempt_count",
                0,
            )
            + 1
        )

        agent_input = SkillGapAgentInput(
            request=state["request"],
            baseline=baseline,
            validation_feedback=state.get(
                "validation_errors",
                [],
            ),
        )

        try:
            result = await runnable.ainvoke(agent_input.to_prompt_payload())

            return {
                "agent_result": result,
                "attempt_count": attempt_count,
                "status": "validating",
                "last_error": None,
            }

        except Exception as exc:
            return {
                "agent_result": None,
                "attempt_count": attempt_count,
                "validation_errors": [(f"Skill Gap Agent invocation failed: {exc}")],
                "status": "retrying",
                "last_error": str(exc),
            }

    async def validate_node(
        state: SkillGapState,
    ) -> dict[str, Any]:
        baseline = state.get("baseline")

        result = state.get("agent_result")

        attempt_count = state.get(
            "attempt_count",
            0,
        )

        max_attempts = state.get(
            "max_attempts",
            2,
        )

        if baseline is None:
            return {
                "status": "failed",
                "last_error": ("Skill-gap baseline is unavailable."),
            }

        if result is None:
            return {"status": ("retrying" if attempt_count < max_attempts else "failed")}

        validation = validate_skill_gap_output(
            state["request"],
            baseline,
            result,
        )

        warnings = _deduplicate(
            [
                *state.get(
                    "warnings",
                    [],
                ),
                *validation.warnings,
            ]
        )

        if validation.is_valid:
            state_for_merge = dict(state)

            state_for_merge["warnings"] = warnings

            final_result = _merge_result(
                cast(
                    SkillGapState,
                    state_for_merge,
                )
            )

            return {
                "final_result": final_result,
                "validation_errors": [],
                "warnings": warnings,
                "status": "completed",
                "last_error": None,
            }

        return {
            "validation_errors": (validation.errors),
            "warnings": warnings,
            "status": ("retrying" if attempt_count < max_attempts else "failed"),
        }

    async def fallback_node(
        state: SkillGapState,
    ) -> dict[str, Any]:
        baseline = state.get("baseline")

        if baseline is None:
            return {
                "status": "failed",
                "last_error": ("Unable to create deterministic Skill Gap fallback."),
            }

        result = build_skill_gap_fallback(
            baseline,
            state["request"],
        )

        return {
            "final_result": result,
            "warnings": list(result.warnings),
            "status": ("completed_with_fallback"),
        }

    async def reject_node(
        state: SkillGapState,
    ) -> dict[str, Any]:
        return {
            "status": "failed",
            "last_error": state.get("last_error"),
        }

    async def finalize_node(
        state: SkillGapState,
    ) -> dict[str, Any]:
        return {
            "status": state.get(
                "status",
                "completed",
            )
        }

    def route_after_baseline(
        state: SkillGapState,
    ) -> Literal[
        "analyze",
        "reject",
    ]:
        if state.get("status") == "failed":
            return "reject"

        return "analyze"

    def route_after_validation(
        state: SkillGapState,
    ) -> Literal[
        "analyze",
        "finalize",
        "fallback",
    ]:
        if state.get("status") == "completed":
            return "finalize"

        if state.get("status") == "retrying" and state.get(
            "attempt_count",
            0,
        ) < state.get(
            "max_attempts",
            2,
        ):
            return "analyze"

        return "fallback"

    builder = StateGraph(SkillGapState)

    builder.add_node(
        "baseline",
        RunnableLambda(baseline_node),
    )

    builder.add_node(
        "analyze",
        RunnableLambda(analyze_node),
    )

    builder.add_node(
        "validate",
        RunnableLambda(validate_node),
    )

    builder.add_node(
        "fallback",
        RunnableLambda(fallback_node),
    )

    builder.add_node(
        "reject",
        RunnableLambda(reject_node),
    )

    builder.add_node(
        "finalize",
        RunnableLambda(finalize_node),
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


async def run_skill_gap_workflow(
    *,
    request: SkillGapRequest,
    runnable: SkillGapRunnable | None = None,
    max_attempts: int = 2,
    thread_id: str | None = None,
) -> SkillGapWorkflowResult:
    """Execute Skill Gap Agent workflow."""

    selected_runnable = runnable if runnable is not None else _create_default_runnable()

    graph = build_skill_gap_workflow(selected_runnable)

    initial_state: SkillGapState = {
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

    raw_result = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": (thread_id or str(uuid4()))}},
    )

    return SkillGapWorkflowResult(
        status=raw_result.get(
            "status",
            "failed",
        ),
        skill_gap=raw_result.get("final_result"),
        agent_analysis=raw_result.get("agent_result"),
        baseline=raw_result.get("baseline"),
        attempt_count=raw_result.get(
            "attempt_count",
            0,
        ),
        validation_errors=raw_result.get(
            "validation_errors",
            [],
        ),
        warnings=raw_result.get(
            "warnings",
            [],
        ),
        last_error=raw_result.get("last_error"),
    )
