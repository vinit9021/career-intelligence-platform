"""LangGraph Cover Letter Agent workflow."""

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
    AgentExecutionError,
)
from app.agents.cover_letter.agent import (
    CoverLetterRunnable,
    build_cover_letter_runnable,
)
from app.agents.cover_letter.state import (
    CoverLetterAgentInput,
    CoverLetterAnalysis,
    CoverLetterRequest,
    CoverLetterResult,
    CoverLetterState,
    CoverLetterWorkflowResult,
)
from app.agents.cover_letter.validator import (
    validate_cover_letter_output,
)
from app.cover_letters.generator import (
    build_cover_letter_fallback,
)
from app.llm.factory import create_chat_model

_AGENT_NAME = "groq_cover_letter_agent"
_AGENT_VERSION = "1.0.0"


def _deduplicate(
    values: list[str],
) -> list[str]:
    return list(dict.fromkeys(values))


def _finalize_agent_result(
    request: CoverLetterRequest,
    analysis: CoverLetterAnalysis,
    validator_warnings: list[str],
) -> CoverLetterResult:
    warnings = _deduplicate(
        [
            *analysis.warnings,
            *validator_warnings,
        ]
    )

    return CoverLetterResult(
        target_role=(request.job_description.job_title),
        company_name=(request.job_description.company_name),
        greeting=analysis.greeting,
        opening_paragraph=(analysis.opening_paragraph),
        body_paragraphs=list(analysis.body_paragraphs),
        closing_paragraph=(analysis.closing_paragraph),
        sign_off=analysis.sign_off,
        full_text=analysis.full_text(),
        skills_mentioned=list(analysis.skills_mentioned),
        evidence=list(analysis.evidence),
        warnings=warnings,
        agent_name=_AGENT_NAME,
        agent_version=_AGENT_VERSION,
        deterministic_fallback=False,
    )


def _build_unavailable_runnable(
    message: str,
) -> CoverLetterRunnable:
    async def unavailable_model(
        _: dict[str, Any],
    ) -> CoverLetterAnalysis:
        raise AgentConfigurationError(message)

    return cast(
        CoverLetterRunnable,
        RunnableLambda(unavailable_model),
    )


def _create_default_runnable() -> CoverLetterRunnable:
    try:
        model = create_chat_model()
    except AgentConfigurationError as exc:
        return _build_unavailable_runnable(str(exc))

    return build_cover_letter_runnable(model)


def build_cover_letter_workflow(
    runnable: CoverLetterRunnable,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Build retryable Cover Letter workflow."""

    async def prepare(
        state: CoverLetterState,
    ) -> dict[str, Any]:
        request = state["request"]

        if not request.resume_raw_text.strip() and not request.resume.model_dump(mode="python"):
            return {
                "status": "failed",
                "last_error": ("Resume content is unavailable."),
            }

        return {
            "status": "generating",
            "last_error": None,
        }

    async def generate(
        state: CoverLetterState,
    ) -> dict[str, Any]:
        attempt_count = (
            state.get(
                "attempt_count",
                0,
            )
            + 1
        )

        agent_input = CoverLetterAgentInput(
            request=state["request"],
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
                "validation_errors": [f"Agent invocation failed: {exc}"],
                "status": "retrying",
                "last_error": str(exc),
            }

    async def validate(
        state: CoverLetterState,
    ) -> dict[str, Any]:
        result = state.get("agent_result")

        attempt_count = state.get(
            "attempt_count",
            0,
        )

        max_attempts = state.get(
            "max_attempts",
            2,
        )

        if result is None:
            return {"status": ("retrying" if attempt_count < max_attempts else "failed")}

        validation = validate_cover_letter_output(
            state["request"],
            result,
        )

        combined_warnings = _deduplicate(
            [
                *state.get(
                    "warnings",
                    [],
                ),
                *validation.warnings,
            ]
        )

        if validation.is_valid:
            final_result = _finalize_agent_result(
                state["request"],
                result,
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
            "validation_errors": (validation.errors),
            "warnings": combined_warnings,
            "status": ("retrying" if attempt_count < max_attempts else "failed"),
        }

    async def fallback(
        state: CoverLetterState,
    ) -> dict[str, Any]:
        try:
            result = build_cover_letter_fallback(state["request"])

            return {
                "final_result": result,
                "warnings": list(result.warnings),
                "status": ("completed_with_fallback"),
            }

        except Exception as exc:
            return {
                "final_result": None,
                "status": "failed",
                "last_error": (f"AI and deterministic cover-letter generation failed: {exc}"),
            }

    async def reject(
        state: CoverLetterState,
    ) -> dict[str, Any]:
        return {
            "status": "failed",
            "last_error": state.get("last_error"),
        }

    async def finalize(
        state: CoverLetterState,
    ) -> dict[str, Any]:
        return {
            "status": state.get(
                "status",
                "completed",
            )
        }

    def route_after_prepare(
        state: CoverLetterState,
    ) -> Literal[
        "generate",
        "reject",
    ]:
        if state.get("status") == "failed":
            return "reject"

        return "generate"

    def route_after_validation(
        state: CoverLetterState,
    ) -> Literal[
        "generate",
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
            return "generate"

        return "fallback"

    builder = StateGraph(CoverLetterState)

    builder.add_node(
        "prepare",
        RunnableLambda(prepare),
    )

    builder.add_node(
        "generate",
        RunnableLambda(generate),
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
        "prepare",
    )

    builder.add_conditional_edges(
        "prepare",
        route_after_prepare,
        {
            "generate": "generate",
            "reject": "reject",
        },
    )

    builder.add_edge(
        "generate",
        "validate",
    )

    builder.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "generate": "generate",
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


async def run_cover_letter_workflow(
    *,
    request: CoverLetterRequest,
    runnable: CoverLetterRunnable | None = None,
    max_attempts: int = 2,
    thread_id: str | None = None,
) -> CoverLetterWorkflowResult:
    """Execute Cover Letter Agent workflow."""

    selected_runnable = runnable if runnable is not None else _create_default_runnable()

    graph = build_cover_letter_workflow(selected_runnable)

    initial_state: CoverLetterState = {
        "request": request,
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

    if not isinstance(
        raw_result,
        dict,
    ):
        raise AgentExecutionError("Cover Letter Agent returned invalid workflow state.")

    return CoverLetterWorkflowResult(
        status=raw_result.get(
            "status",
            "failed",
        ),
        cover_letter=raw_result.get("final_result"),
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
