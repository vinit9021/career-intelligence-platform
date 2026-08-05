"""LangGraph orchestration for the Resume Parser AI Agent."""

from __future__ import annotations

from typing import Any, Literal, cast
from uuid import uuid4

from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.base.errors import (
    AgentConfigurationError,
    AgentExecutionError,
)
from app.agents.resume_parser.agent import (
    ResumeParserRunnable,
    build_resume_parser_runnable,
)
from app.agents.resume_parser.state import (
    ResumeParserAgentInput,
    ResumeParserState,
    ResumeParserWorkflowResult,
)
from app.agents.resume_parser.validator import (
    validate_resume_output,
)
from app.llm.factory import create_chat_model
from app.schemas.resume_parsing import ResumeStructuredContent

_MINIMUM_RESUME_TEXT_LENGTH = 80


def _build_unavailable_runnable(
    message: str,
) -> ResumeParserRunnable:
    async def unavailable_model(
        _: dict[str, Any],
    ) -> ResumeStructuredContent:
        raise AgentConfigurationError(message)

    return cast(
        ResumeParserRunnable,
        RunnableLambda(unavailable_model),
    )


def _create_default_runnable() -> ResumeParserRunnable:
    try:
        model = create_chat_model()
    except AgentConfigurationError as exc:
        return _build_unavailable_runnable(str(exc))

    return build_resume_parser_runnable(model)


def build_resume_parser_workflow(
    runnable: ResumeParserRunnable,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Build the retryable LangGraph resume-parser workflow."""

    async def assess_text(
        state: ResumeParserState,
    ) -> dict[str, Any]:
        resume_text = state.get(
            "resume_text",
            "",
        ).strip()

        requires_ocr = len(resume_text) < _MINIMUM_RESUME_TEXT_LENGTH

        return {
            "resume_text": resume_text,
            "requires_ocr": requires_ocr,
            "status": ("needs_ocr" if requires_ocr else "analyzing"),
        }

    async def analyze(
        state: ResumeParserState,
    ) -> dict[str, Any]:
        attempt_count = (
            state.get(
                "attempt_count",
                0,
            )
            + 1
        )

        agent_input = ResumeParserAgentInput(
            resume_text=state.get(
                "resume_text",
                "",
            ),
            baseline_result=state.get(
                "baseline_result",
                {},
            ),
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
        state: ResumeParserState,
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

        validation = validate_resume_output(
            state.get(
                "resume_text",
                "",
            ),
            result,
        )

        combined_warnings = list(
            dict.fromkeys(
                [
                    *state.get(
                        "warnings",
                        [],
                    ),
                    *validation.warnings,
                ]
            )
        )

        if validation.is_valid:
            return {
                "final_result": result,
                "validation_errors": [],
                "warnings": combined_warnings,
                "status": "completed",
            }

        return {
            "validation_errors": validation.errors,
            "warnings": combined_warnings,
            "status": ("retrying" if attempt_count < max_attempts else "failed"),
        }

    async def fallback(
        state: ResumeParserState,
    ) -> dict[str, Any]:
        baseline_result = state.get(
            "baseline_result",
            {},
        )

        try:
            fallback_result = ResumeStructuredContent.model_validate(baseline_result)
        except Exception as exc:
            return {
                "final_result": None,
                "status": "failed",
                "last_error": (
                    f"The AI agent failed and the deterministic fallback was invalid: {exc}"
                ),
            }

        fallback_warning = (
            "AI resume parsing was unavailable or invalid. "
            "The deterministic parser result was used."
        )

        return {
            "final_result": fallback_result,
            "warnings": list(
                dict.fromkeys(
                    [
                        *state.get(
                            "warnings",
                            [],
                        ),
                        fallback_warning,
                    ]
                )
            ),
            "status": "completed_with_fallback",
        }

    async def mark_needs_ocr(
        _: ResumeParserState,
    ) -> dict[str, Any]:
        return {
            "requires_ocr": True,
            "status": "needs_ocr",
            "warnings": [
                "The extracted resume text is too short and the document may require OCR."
            ],
        }

    async def finalize(
        state: ResumeParserState,
    ) -> dict[str, Any]:
        return {
            "status": state.get(
                "status",
                "completed",
            )
        }

    def route_after_assessment(
        state: ResumeParserState,
    ) -> Literal["analyze", "needs_ocr"]:
        if state.get(
            "requires_ocr",
            False,
        ):
            return "needs_ocr"

        return "analyze"

    def route_after_validation(
        state: ResumeParserState,
    ) -> Literal[
        "analyze",
        "finalize",
        "fallback",
    ]:
        status = state.get(
            "status",
            "failed",
        )

        if status == "completed":
            return "finalize"

        attempt_count = state.get(
            "attempt_count",
            0,
        )

        max_attempts = state.get(
            "max_attempts",
            2,
        )

        if status == "retrying" and attempt_count < max_attempts:
            return "analyze"

        return "fallback"

    builder = StateGraph(ResumeParserState)

    builder.add_node(
        "assess_text",
        assess_text,
    )

    builder.add_node(
        "analyze",
        analyze,
    )

    builder.add_node(
        "validate",
        validate,
    )

    builder.add_node(
        "fallback",
        fallback,
    )

    builder.add_node(
        "needs_ocr",
        RunnableLambda(mark_needs_ocr),
    )

    builder.add_node(
        "finalize",
        finalize,
    )

    builder.add_edge(
        START,
        "assess_text",
    )

    builder.add_conditional_edges(
        "assess_text",
        route_after_assessment,
        {
            "analyze": "analyze",
            "needs_ocr": "needs_ocr",
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
        "needs_ocr",
        END,
    )

    if use_checkpointer:
        return builder.compile(checkpointer=InMemorySaver())

    return builder.compile()


async def run_resume_parser_workflow(
    *,
    resume_text: str,
    baseline_result: dict[str, Any] | None = None,
    runnable: ResumeParserRunnable | None = None,
    max_attempts: int = 2,
    thread_id: str | None = None,
) -> ResumeParserWorkflowResult:
    """Execute the Resume Parser Agent workflow."""

    selected_runnable = runnable if runnable is not None else _create_default_runnable()

    graph = build_resume_parser_workflow(selected_runnable)

    initial_state: ResumeParserState = {
        "resume_text": resume_text,
        "baseline_result": baseline_result or {},
        "agent_result": None,
        "final_result": None,
        "attempt_count": 0,
        "max_attempts": max_attempts,
        "validation_errors": [],
        "warnings": [],
        "status": "pending",
        "last_error": None,
        "requires_ocr": False,
    }

    configuration = {
        "configurable": {"thread_id": (thread_id if thread_id is not None else str(uuid4()))}
    }

    raw_result = await graph.ainvoke(
        initial_state,
        config=configuration,
    )

    if not isinstance(raw_result, dict):
        raise AgentExecutionError("Resume Parser Agent returned invalid workflow state.")

    final_result = raw_result.get("final_result")

    if final_result is not None and not isinstance(
        final_result,
        ResumeStructuredContent,
    ):
        final_result = ResumeStructuredContent.model_validate(final_result)

    return ResumeParserWorkflowResult(
        status=raw_result.get(
            "status",
            "failed",
        ),
        structured_resume=final_result,
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
        requires_ocr=raw_result.get(
            "requires_ocr",
            False,
        ),
        last_error=raw_result.get("last_error"),
    )
