"""Adapters connecting real agent workflows to central LangGraph."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Any, cast, get_type_hints

from pydantic import BaseModel

from app.orchestration.registry import (
    AgentExecutor,
    AgentRegistry,
)
from app.orchestration.serialization import (
    to_checkpoint_value,
)
from app.orchestration.state import (
    AgentNodeName,
    AgentNodeResult,
    CareerWorkflowState,
)

WorkflowRunner = Callable[
    ...,
    Awaitable[Any],
]

_COMPLETED_STATUSES = {
    "completed",
    "completed_with_fallback",
}


@dataclass(frozen=True)
class RealAgentWorkflows:
    """Concrete workflow runners."""

    resume_parser: WorkflowRunner

    job_description_analyzer: WorkflowRunner

    resume_matching: WorkflowRunner

    ats_optimization: WorkflowRunner

    skill_gap: WorkflowRunner

    cover_letter: WorkflowRunner

    resume_version_manager: WorkflowRunner | None = None


def _load_runner(
    modules: tuple[str, ...],
    names: tuple[str, ...],
) -> WorkflowRunner:
    """Load first available workflow runner."""

    errors: list[str] = []

    for module_name in modules:
        try:
            module = import_module(module_name)

        except ImportError as exc:
            errors.append(f"{module_name}: {exc}")
            continue

        for name in names:
            value = getattr(
                module,
                name,
                None,
            )

            if callable(value):
                return cast(
                    WorkflowRunner,
                    value,
                )

    raise ImportError(
        "Unable to locate workflow runner. "
        f"Modules={modules}, names={names}. "
        f"Errors={'; '.join(errors)}"
    )


def load_real_agent_workflows(
    *,
    include_resume_version_manager: bool = False,
) -> RealAgentWorkflows:
    """Load real workflows from previous days."""

    resume_parser = _load_runner(
        ("app.workflows.resume_parser",),
        ("run_resume_parser_workflow",),
    )

    job_description_analyzer = _load_runner(
        ("app.workflows.job_description_analyzer",),
        ("run_job_description_analyzer_workflow",),
    )

    resume_matching = _load_runner(
        (
            "app.workflows.resume_matching_agent",
            "app.workflows.resume_matching",
        ),
        (
            "run_resume_matching_agent_workflow",
            "run_resume_matching_workflow",
        ),
    )

    ats_optimization = _load_runner(
        ("app.workflows.ats_optimization",),
        ("run_ats_optimization_workflow",),
    )

    skill_gap = _load_runner(
        ("app.workflows.skill_gap",),
        ("run_skill_gap_workflow",),
    )

    cover_letter = _load_runner(
        ("app.workflows.cover_letter",),
        ("run_cover_letter_workflow",),
    )

    resume_version_manager: WorkflowRunner | None = None

    if include_resume_version_manager:
        resume_version_manager = _load_runner(
            ("app.workflows.resume_version_manager",),
            ("run_resume_version_manager_workflow",),
        )

    return RealAgentWorkflows(
        resume_parser=resume_parser,
        job_description_analyzer=(job_description_analyzer),
        resume_matching=resume_matching,
        ats_optimization=ats_optimization,
        skill_gap=skill_gap,
        cover_letter=cover_letter,
        resume_version_manager=(resume_version_manager),
    )


def _context(
    state: CareerWorkflowState,
) -> dict[str, Any]:
    return state.get(
        "context",
        {},
    )


def _outputs(
    state: CareerWorkflowState,
) -> dict[str, Any]:
    return state.get(
        "outputs",
        {},
    )


def _require(
    value: Any,
    message: str,
) -> Any:
    if value is None:
        raise ValueError(message)

    if isinstance(value, str) and not value.strip():
        raise ValueError(message)

    return value


def _type_hints(
    runner: WorkflowRunner,
) -> dict[str, Any]:
    try:
        return get_type_hints(runner)

    except Exception:
        return {}


def _is_pydantic_model(
    annotation: Any,
) -> bool:
    try:
        return isinstance(annotation, type) and issubclass(
            annotation,
            BaseModel,
        )

    except TypeError:
        return False


def _coerce_argument(
    runner: WorkflowRunner,
    name: str,
    value: Any,
) -> Any:
    annotation = _type_hints(runner).get(name)

    if (
        annotation is not None
        and _is_pydantic_model(annotation)
        and not isinstance(
            value,
            annotation,
        )
    ):
        return annotation.model_validate(value)

    return value


def _build_request_model(
    runner: WorkflowRunner,
    name: str,
    payload: dict[str, Any],
) -> Any:
    annotation = _type_hints(runner).get(name)

    if annotation is None or not _is_pydantic_model(annotation):
        raise TypeError(f"Unable to determine Pydantic request model for {name}.")

    return annotation.model_validate(payload)


async def _invoke_workflow(
    runner: WorkflowRunner,
    payload: dict[str, Any],
) -> Any:
    """Invoke workflow according to its signature."""

    signature = inspect.signature(runner)

    kwargs: dict[str, Any] = {}

    for name, parameter in signature.parameters.items():
        if name in payload:
            kwargs[name] = _coerce_argument(
                runner,
                name,
                payload[name],
            )
            continue

        if name == "request":
            kwargs[name] = _build_request_model(
                runner,
                name,
                payload,
            )
            continue

        if parameter.default is not inspect.Parameter.empty:
            continue

        raise ValueError(f"Missing required workflow argument: {name}")

    return await runner(**kwargs)


def _result_value(
    result: Any,
    name: str,
) -> Any:
    if isinstance(
        result,
        dict,
    ):
        return result.get(name)

    return getattr(
        result,
        name,
        None,
    )


def _result_list(
    result: Any,
    name: str,
) -> list[str]:
    value = _result_value(
        result,
        name,
    )

    if not isinstance(
        value,
        list,
    ):
        return []

    return [str(item) for item in value]


def _extract_output(
    result: Any,
    candidates: tuple[str, ...],
) -> Any:
    for name in candidates:
        value = _result_value(
            result,
            name,
        )

        if value is not None:
            return value

    return result


def _normalize_result(
    *,
    result: Any,
    output_fields: tuple[str, ...],
) -> AgentNodeResult:
    status = _result_value(
        result,
        "status",
    )

    warnings = _result_list(
        result,
        "warnings",
    )

    validation_errors = _result_list(
        result,
        "validation_errors",
    )

    last_error = _result_value(
        result,
        "last_error",
    )

    status_text = None if status is None else str(status)

    if status_text is None or status_text in _COMPLETED_STATUSES:
        try:
            output = to_checkpoint_value(
                _extract_output(
                    result,
                    output_fields,
                )
            )

        except TypeError as exc:
            return AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=False,
            )

        return AgentNodeResult(
            status="completed",
            output=output,
            warnings=warnings,
        )

    message = (
        str(last_error)
        if last_error
        else (
            validation_errors[0]
            if validation_errors
            else (f"Agent workflow returned status {status_text}.")
        )
    )

    return AgentNodeResult(
        status="failed",
        warnings=warnings,
        error=message,
        retryable=True,
    )


def _common_payload(
    state: CareerWorkflowState,
) -> dict[str, Any]:
    context = _context(state)

    return {
        **context,
        "max_attempts": context.get(
            "agent_max_attempts",
            2,
        ),
    }


def _resume_parser_executor(
    runner: WorkflowRunner,
) -> AgentExecutor:
    async def execute(
        state: CareerWorkflowState,
    ) -> AgentNodeResult:
        context = _context(state)

        raw_text = _require(
            context.get("resume_raw_text") or context.get("resume_text"),
            "resume_raw_text is required.",
        )

        payload = {
            **_common_payload(state),
            "text": raw_text,
            "raw_text": raw_text,
            "resume_text": raw_text,
        }

        try:
            result = await _invoke_workflow(
                runner,
                payload,
            )

        except Exception as exc:
            return AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=True,
            )

        return _normalize_result(
            result=result,
            output_fields=(
                "resume",
                "parsed_resume",
                "resume_content",
                "final_result",
            ),
        )

    return execute


def _job_description_executor(
    runner: WorkflowRunner,
) -> AgentExecutor:
    async def execute(
        state: CareerWorkflowState,
    ) -> AgentNodeResult:
        context = _context(state)

        text = _require(
            context.get("job_description_text") or context.get("job_text"),
            ("job_description_text is required."),
        )

        payload = {
            **_common_payload(state),
            "text": text,
            "raw_text": text,
            "job_description_text": text,
        }

        try:
            result = await _invoke_workflow(
                runner,
                payload,
            )

        except Exception as exc:
            return AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=True,
            )

        return _normalize_result(
            result=result,
            output_fields=(
                "job_description",
                "parsed_job_description",
                "final_result",
            ),
        )

    return execute


def _resume_matching_executor(
    runner: WorkflowRunner,
) -> AgentExecutor:
    async def execute(
        state: CareerWorkflowState,
    ) -> AgentNodeResult:
        context = _context(state)
        outputs = _outputs(state)

        resume = _require(
            outputs.get("resume_parser"),
            ("Resume Matching requires Resume Parser output."),
        )

        job_description = _require(
            outputs.get("job_description_analyzer"),
            ("Resume Matching requires JD Analyzer output."),
        )

        payload = {
            **_common_payload(state),
            "resume": resume,
            "job_description": (job_description),
            "resume_raw_text": context.get(
                "resume_raw_text",
                "",
            ),
        }

        try:
            result = await _invoke_workflow(
                runner,
                payload,
            )

        except Exception as exc:
            return AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=True,
            )

        return _normalize_result(
            result=result,
            output_fields=(
                "match_result",
                "resume_match",
                "matching_result",
                "final_result",
            ),
        )

    return execute


def _ats_executor(
    runner: WorkflowRunner,
) -> AgentExecutor:
    async def execute(
        state: CareerWorkflowState,
    ) -> AgentNodeResult:
        context = _context(state)
        outputs = _outputs(state)

        resume = _require(
            outputs.get("resume_parser"),
            ("ATS Optimization requires Resume Parser output."),
        )

        job_description = _require(
            outputs.get("job_description_analyzer"),
            ("ATS Optimization requires JD Analyzer output."),
        )

        match_result = _require(
            outputs.get("resume_matching"),
            ("ATS Optimization requires Resume Matching output."),
        )

        payload = {
            **_common_payload(state),
            "resume": resume,
            "job_description": (job_description),
            "match_result": match_result,
            "resume_raw_text": context.get(
                "resume_raw_text",
                "",
            ),
            "max_bullet_rewrites": (
                context.get(
                    "max_bullet_rewrites",
                    5,
                )
            ),
        }

        try:
            result = await _invoke_workflow(
                runner,
                payload,
            )

        except Exception as exc:
            return AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=True,
            )

        return _normalize_result(
            result=result,
            output_fields=(
                "optimization",
                "ats_optimization",
                "optimization_result",
                "result",
                "final_result",
            ),
        )

    return execute


def _skill_gap_executor(
    runner: WorkflowRunner,
) -> AgentExecutor:
    async def execute(
        state: CareerWorkflowState,
    ) -> AgentNodeResult:
        context = _context(state)
        outputs = _outputs(state)

        resume = _require(
            outputs.get("resume_parser"),
            ("Skill Gap requires Resume Parser output."),
        )

        job_description = _require(
            outputs.get("job_description_analyzer"),
            ("Skill Gap requires JD Analyzer output."),
        )

        match_result = _require(
            outputs.get("resume_matching"),
            ("Skill Gap requires Resume Matching output."),
        )

        payload = {
            **_common_payload(state),
            "resume": resume,
            "job_description": (job_description),
            "match_result": match_result,
            "resume_raw_text": context.get(
                "resume_raw_text",
                "",
            ),
            "max_roadmap_steps": (
                context.get(
                    "max_roadmap_steps",
                    8,
                )
            ),
            "max_mini_projects": (
                context.get(
                    "max_mini_projects",
                    3,
                )
            ),
        }

        try:
            result = await _invoke_workflow(
                runner,
                payload,
            )

        except Exception as exc:
            return AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=True,
            )

        return _normalize_result(
            result=result,
            output_fields=(
                "skill_gap",
                "result",
                "final_result",
            ),
        )

    return execute


def _cover_letter_executor(
    runner: WorkflowRunner,
) -> AgentExecutor:
    async def execute(
        state: CareerWorkflowState,
    ) -> AgentNodeResult:
        context = _context(state)
        outputs = _outputs(state)

        resume = _require(
            outputs.get("resume_parser"),
            ("Cover Letter requires Resume Parser output."),
        )

        job_description = _require(
            outputs.get("job_description_analyzer"),
            ("Cover Letter requires JD Analyzer output."),
        )

        match_result = _require(
            outputs.get("resume_matching"),
            ("Cover Letter requires Resume Matching output."),
        )

        payload = {
            **_common_payload(state),
            "resume": resume,
            "job_description": (job_description),
            "match_result": match_result,
            "resume_raw_text": context.get(
                "resume_raw_text",
                "",
            ),
            "candidate_name": context.get("candidate_name"),
            "company_context": context.get("company_context"),
            "tone": context.get(
                "cover_letter_tone",
                "professional",
            ),
            "max_words": context.get(
                "cover_letter_max_words",
                300,
            ),
        }

        try:
            result = await _invoke_workflow(
                runner,
                payload,
            )

        except Exception as exc:
            return AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=True,
            )

        return _normalize_result(
            result=result,
            output_fields=(
                "cover_letter",
                "result",
                "final_result",
            ),
        )

    return execute


def _resume_version_executor(
    runner: WorkflowRunner,
    agent: Any,
) -> AgentExecutor:
    """Keep service dependency outside graph state."""

    async def execute(
        state: CareerWorkflowState,
    ) -> AgentNodeResult:
        context = _context(state)

        request = _require(
            context.get("resume_version_request"),
            ("resume_version_request is required when Resume Version Manager is enabled."),
        )

        payload = {
            **_common_payload(state),
            "agent": agent,
            "request": request,
        }

        try:
            result = await _invoke_workflow(
                runner,
                payload,
            )

        except Exception as exc:
            return AgentNodeResult(
                status="failed",
                error=str(exc),
                retryable=True,
            )

        return _normalize_result(
            result=result,
            output_fields=(
                "version",
                "submission",
                "result",
                "final_result",
            ),
        )

    return execute


def build_real_agent_registry(
    workflows: RealAgentWorkflows,
    *,
    include_resume_version_manager: bool = False,
    resume_version_agent: Any = None,
) -> AgentRegistry:
    """Register real agents."""

    registry = AgentRegistry()

    registry.register(
        "resume_parser",
        _resume_parser_executor(workflows.resume_parser),
    )

    registry.register(
        "job_description_analyzer",
        _job_description_executor(workflows.job_description_analyzer),
    )

    registry.register(
        "resume_matching",
        _resume_matching_executor(workflows.resume_matching),
    )

    registry.register(
        "ats_optimization",
        _ats_executor(workflows.ats_optimization),
    )

    registry.register(
        "skill_gap",
        _skill_gap_executor(workflows.skill_gap),
    )

    registry.register(
        "cover_letter",
        _cover_letter_executor(workflows.cover_letter),
    )

    if include_resume_version_manager:
        runner = workflows.resume_version_manager

        if runner is None:
            raise ValueError(
                "Resume Version Manager was requested but no workflow runner was supplied."
            )

        if resume_version_agent is None:
            raise ValueError(
                "resume_version_agent is required when Resume Version Manager is enabled."
            )

        registry.register(
            "resume_version_manager",
            _resume_version_executor(
                runner,
                resume_version_agent,
            ),
        )

    return registry


def registered_real_nodes(
    registry: AgentRegistry,
) -> list[AgentNodeName]:
    """Return registered production nodes."""

    nodes: list[AgentNodeName] = [
        "resume_parser",
        "job_description_analyzer",
        "resume_matching",
        "ats_optimization",
        "skill_gap",
        "cover_letter",
    ]

    if registry.contains("resume_version_manager"):
        nodes.append("resume_version_manager")

    return nodes
