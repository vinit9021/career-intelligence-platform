"""LangGraph Job Description Analyzer workflow."""

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
from app.agents.job_description_analyzer.agent import (
    JobDescriptionAnalyzerRunnable,
    build_job_description_analyzer_runnable,
)
from app.agents.job_description_analyzer.state import (
    JobDescriptionAnalyzerInput,
    JobDescriptionAnalyzerState,
    JobDescriptionAnalyzerWorkflowResult,
)
from app.agents.job_description_analyzer.validator import (
    validate_job_description_output,
)
from app.llm.factory import create_chat_model
from app.parsers import JobDescriptionParser
from app.schemas.job_description_parser import ParsedJobDescription

_MINIMUM_JOB_DESCRIPTION_LENGTH = 40
_AGENT_NAME = "groq_job_description_analyzer"
_AGENT_VERSION = "1.0.0"


def _normalize_text(value: str) -> str:
    lines = (
        value.replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
        .split("\n")
    )

    normalized_lines: list[str] = []
    previous_blank = False

    for line in lines:
        stripped = line.strip()
        is_blank = not stripped

        if is_blank and previous_blank:
            continue

        normalized_lines.append(stripped)
        previous_blank = is_blank

    return "\n".join(normalized_lines).strip()


def _build_unavailable_runnable(
    message: str,
) -> JobDescriptionAnalyzerRunnable:
    async def unavailable_model(
        _: dict[str, Any],
    ) -> ParsedJobDescription:
        raise AgentConfigurationError(message)

    return cast(
        JobDescriptionAnalyzerRunnable,
        RunnableLambda(unavailable_model),
    )


def _create_default_runnable() -> JobDescriptionAnalyzerRunnable:
    try:
        model = create_chat_model()
    except AgentConfigurationError as exc:
        return _build_unavailable_runnable(str(exc))

    return build_job_description_analyzer_runnable(model)


def _finalize_agent_result(
    result: ParsedJobDescription,
    normalized_text: str,
    validation_warnings: list[str],
) -> ParsedJobDescription:
    combined_warnings = list(
        dict.fromkeys(
            [
                *result.metadata.warnings,
                *validation_warnings,
            ]
        )
    )

    metadata = result.metadata.model_copy(
        update={
            "parser_name": _AGENT_NAME,
            "parser_version": _AGENT_VERSION,
            "character_count": len(normalized_text),
            "warnings": combined_warnings,
        }
    )

    return result.model_copy(
        update={
            "normalized_text": normalized_text,
            "metadata": metadata,
        }
    )


def _finalize_fallback_result(
    result: ParsedJobDescription,
    normalized_text: str,
) -> ParsedJobDescription:
    fallback_warning = (
        "AI job-description analysis was unavailable or "
        "invalid. The deterministic parser result was used."
    )

    warnings = list(
        dict.fromkeys(
            [
                *result.metadata.warnings,
                fallback_warning,
            ]
        )
    )

    metadata = result.metadata.model_copy(
        update={
            "character_count": len(normalized_text),
            "warnings": warnings,
        }
    )

    return result.model_copy(
        update={
            "normalized_text": normalized_text,
            "metadata": metadata,
        }
    )


def build_job_description_analyzer_workflow(
    runnable: JobDescriptionAnalyzerRunnable,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Build the LangGraph workflow."""

    async def normalize_input(
        state: JobDescriptionAnalyzerState,
    ) -> dict[str, Any]:
        normalized_text = _normalize_text(
            state.get(
                "job_description_text",
                "",
            )
        )

        if len(normalized_text) < _MINIMUM_JOB_DESCRIPTION_LENGTH:
            return {
                "normalized_text": normalized_text,
                "status": "failed",
                "last_error": ("The job description is too short to analyze."),
            }

        return {
            "normalized_text": normalized_text,
            "status": "baselining",
            "last_error": None,
        }

    async def create_baseline(
        state: JobDescriptionAnalyzerState,
    ) -> dict[str, Any]:
        normalized_text = state.get(
            "normalized_text",
            "",
        )

        try:
            baseline = JobDescriptionParser().parse(normalized_text)

            return {
                "baseline_result": baseline.model_dump(mode="python"),
                "status": "analyzing",
                "last_error": None,
            }
        except Exception as exc:
            return {
                "baseline_result": {},
                "status": "analyzing",
                "warnings": [f"The deterministic parser failed: {exc}"],
                "last_error": None,
            }

    async def analyze(
        state: JobDescriptionAnalyzerState,
    ) -> dict[str, Any]:
        attempt_count = (
            state.get(
                "attempt_count",
                0,
            )
            + 1
        )

        agent_input = JobDescriptionAnalyzerInput(
            job_description_text=state.get(
                "normalized_text",
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
        state: JobDescriptionAnalyzerState,
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

        validation = validate_job_description_output(
            state.get(
                "normalized_text",
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
            final_result = _finalize_agent_result(
                result,
                state.get(
                    "normalized_text",
                    "",
                ),
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
        state: JobDescriptionAnalyzerState,
    ) -> dict[str, Any]:
        baseline_result = state.get(
            "baseline_result",
            {},
        )

        try:
            parsed_baseline = ParsedJobDescription.model_validate(baseline_result)
        except Exception as exc:
            return {
                "final_result": None,
                "status": "failed",
                "last_error": (f"AI analysis and deterministic fallback both failed: {exc}"),
            }

        final_result = _finalize_fallback_result(
            parsed_baseline,
            state.get(
                "normalized_text",
                "",
            ),
        )

        return {
            "final_result": final_result,
            "warnings": list(final_result.metadata.warnings),
            "status": "completed_with_fallback",
        }

    async def reject_input(
        state: JobDescriptionAnalyzerState,
    ) -> dict[str, Any]:
        return {
            "status": "failed",
            "last_error": state.get("last_error"),
        }

    async def finalize(
        state: JobDescriptionAnalyzerState,
    ) -> dict[str, Any]:
        return {
            "status": state.get(
                "status",
                "completed",
            )
        }

    def route_after_normalization(
        state: JobDescriptionAnalyzerState,
    ) -> Literal["baseline", "reject"]:
        if state.get("status") == "failed":
            return "reject"

        return "baseline"

    def route_after_validation(
        state: JobDescriptionAnalyzerState,
    ) -> Literal[
        "analyze",
        "finalize",
        "fallback",
    ]:
        if state.get("status") == "completed":
            return "finalize"

        attempt_count = state.get(
            "attempt_count",
            0,
        )

        max_attempts = state.get(
            "max_attempts",
            2,
        )

        if state.get("status") == "retrying" and attempt_count < max_attempts:
            return "analyze"

        return "fallback"

    builder = StateGraph(JobDescriptionAnalyzerState)

    builder.add_node(
        "normalize",
        RunnableLambda(normalize_input),
    )
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
        RunnableLambda(reject_input),
    )
    builder.add_node(
        "finalize",
        RunnableLambda(finalize),
    )

    builder.add_edge(
        START,
        "normalize",
    )

    builder.add_conditional_edges(
        "normalize",
        route_after_normalization,
        {
            "baseline": "baseline",
            "reject": "reject",
        },
    )

    builder.add_edge(
        "baseline",
        "analyze",
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


async def run_job_description_analyzer_workflow(
    *,
    job_description_text: str,
    runnable: (JobDescriptionAnalyzerRunnable | None) = None,
    max_attempts: int = 2,
    thread_id: str | None = None,
) -> JobDescriptionAnalyzerWorkflowResult:
    """Run the Job Description Analyzer workflow."""

    selected_runnable = runnable if runnable is not None else _create_default_runnable()

    graph = build_job_description_analyzer_workflow(selected_runnable)

    initial_state: JobDescriptionAnalyzerState = {
        "job_description_text": job_description_text,
        "normalized_text": "",
        "baseline_result": {},
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
        raise AgentExecutionError("The workflow returned invalid state.")

    return JobDescriptionAnalyzerWorkflowResult(
        status=raw_result.get(
            "status",
            "failed",
        ),
        analyzed_job=raw_result.get("final_result"),
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
