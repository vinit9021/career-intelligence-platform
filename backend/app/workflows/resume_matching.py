"""LangGraph Resume Matching AI Agent workflow."""

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
from app.agents.resume_matching.agent import (
    ResumeMatchingRunnable,
    build_resume_matching_runnable,
)
from app.agents.resume_matching.state import (
    ResumeMatchingAgentInput,
    ResumeMatchingAgentState,
    ResumeMatchingAgentWorkflowResult,
    SemanticResumeMatchingAnalysis,
)
from app.agents.resume_matching.validator import (
    validate_semantic_match_output,
)
from app.llm.factory import create_chat_model
from app.matching import match_resume_to_job
from app.schemas.resume_matching import (
    MatchCategoryScore,
    RequirementEvidence,
    ResponsibilityMatch,
    ResumeJobMatchRequest,
    ResumeJobMatchResult,
    ResumeMatchingMetadata,
)

_AGENT_NAME = "hybrid_groq_resume_matching_agent"
_AGENT_VERSION = "2.0.0"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _deduplicate(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _percentage(
    matched_count: int,
    total_count: int,
    fallback: float,
) -> float:
    if total_count == 0:
        return fallback

    return round(
        matched_count / total_count * 100,
        2,
    )


def _apply_semantic_matches(
    matched: list[str],
    missing: list[str],
    semantic_requirements: set[str],
) -> tuple[list[str], list[str]]:
    updated_matched = list(matched)
    updated_missing: list[str] = []

    matched_keys = {_normalize(value) for value in updated_matched}

    for requirement in missing:
        key = _normalize(requirement)

        if key in semantic_requirements:
            if key not in matched_keys:
                updated_matched.append(requirement)
                matched_keys.add(key)
        else:
            updated_missing.append(requirement)

    return (
        _deduplicate(updated_matched),
        _deduplicate(updated_missing),
    )


def _semantic_requirement_evidence(
    analysis: SemanticResumeMatchingAnalysis,
) -> list[RequirementEvidence]:
    return [
        RequirementEvidence(
            requirement=item.requirement,
            matched_term=item.explanation,
            source_sections=[item.source_section],
            excerpts=[item.resume_excerpt],
        )
        for item in analysis.semantic_requirement_evidence
        if item.confidence >= 0.6
    ]


def _semantic_responsibilities(
    analysis: SemanticResumeMatchingAnalysis,
) -> list[ResponsibilityMatch]:
    return [
        ResponsibilityMatch(
            responsibility=item.responsibility,
            status=item.status,
            score=item.score,
            evidence=item.resume_excerpt,
        )
        for item in analysis.responsibility_alignment
    ]


def _responsibility_score(
    baseline: ResumeJobMatchResult,
    analysis: SemanticResumeMatchingAnalysis,
) -> float:
    semantic_scores = [item.score for item in analysis.responsibility_alignment]

    if semantic_scores:
        semantic_responsibility_score = sum(semantic_scores) / len(semantic_scores)
    else:
        semantic_responsibility_score = analysis.overall_semantic_score

    semantic_component = (semantic_responsibility_score + analysis.overall_semantic_score) / 2

    return round(
        baseline.responsibility_score * 0.35 + semantic_component * 0.65,
        2,
    )


def _update_breakdown(
    baseline: ResumeJobMatchResult,
    *,
    required_score: float,
    preferred_score: float,
    technology_score: float,
    keyword_score: float,
    responsibility_score: float,
) -> list[MatchCategoryScore]:
    category_scores = {
        "required_skills": required_score,
        "preferred_skills": preferred_score,
        "technologies": technology_score,
        "ats_keywords": keyword_score,
        "experience": baseline.experience_score,
        "education": baseline.education_score,
        "responsibilities": responsibility_score,
    }

    updated: list[MatchCategoryScore] = []

    for item in baseline.scoring_breakdown:
        raw_score = category_scores[item.category]

        explanation = item.explanation

        if item.category in {
            "required_skills",
            "preferred_skills",
            "technologies",
            "ats_keywords",
        }:
            explanation = "Hybrid exact, alias-aware and semantic resume evidence matching."

        if item.category == "responsibilities":
            explanation = "Hybrid deterministic and Groq semantic responsibility alignment."

        weighted_points = raw_score * item.effective_weight if item.applicable else 0.0

        updated.append(
            item.model_copy(
                update={
                    "raw_score": round(
                        raw_score,
                        2,
                    ),
                    "weighted_points": round(
                        weighted_points,
                        2,
                    ),
                    "explanation": explanation,
                }
            )
        )

    return updated


def _merge_results(
    request: ResumeJobMatchRequest,
    baseline: ResumeJobMatchResult,
    analysis: SemanticResumeMatchingAnalysis,
    validator_warnings: list[str],
) -> ResumeJobMatchResult:
    semantic_requirements = {
        _normalize(item.requirement)
        for item in analysis.semantic_requirement_evidence
        if item.confidence >= 0.6
    }

    matched_required, missing_required = _apply_semantic_matches(
        baseline.matched_required_skills,
        baseline.missing_required_skills,
        semantic_requirements,
    )

    matched_preferred, missing_preferred = _apply_semantic_matches(
        baseline.matched_preferred_skills,
        baseline.missing_preferred_skills,
        semantic_requirements,
    )

    matched_technologies, missing_technologies = _apply_semantic_matches(
        baseline.matched_technologies,
        baseline.missing_technologies,
        semantic_requirements,
    )

    matched_keywords, missing_keywords = _apply_semantic_matches(
        baseline.matched_keywords,
        baseline.missing_keywords,
        semantic_requirements,
    )

    required_score = _percentage(
        len(matched_required),
        len(matched_required) + len(missing_required),
        baseline.required_skills_score,
    )

    preferred_score = _percentage(
        len(matched_preferred),
        len(matched_preferred) + len(missing_preferred),
        baseline.preferred_skills_score,
    )

    technology_score = _percentage(
        len(matched_technologies),
        len(matched_technologies) + len(missing_technologies),
        baseline.technology_score,
    )

    keyword_score = _percentage(
        len(matched_keywords),
        len(matched_keywords) + len(missing_keywords),
        baseline.keyword_score,
    )

    responsibility_score = _responsibility_score(
        baseline,
        analysis,
    )

    breakdown = _update_breakdown(
        baseline,
        required_score=required_score,
        preferred_score=preferred_score,
        technology_score=technology_score,
        keyword_score=keyword_score,
        responsibility_score=responsibility_score,
    )

    overall_score = round(
        sum(item.weighted_points for item in breakdown),
        2,
    )

    semantic_evidence = _semantic_requirement_evidence(analysis)

    responsibilities = _semantic_responsibilities(analysis)

    if not responsibilities:
        responsibilities = list(baseline.responsibility_alignment)

    evidence = [
        *baseline.resume_evidence,
        *semantic_evidence,
    ]

    metadata = ResumeMatchingMetadata(
        engine_name=_AGENT_NAME,
        engine_version=_AGENT_VERSION,
        deterministic=False,
        compared_requirements=(baseline.metadata.compared_requirements),
        generated_evidence_items=len(evidence),
    )

    warnings = _deduplicate(
        [
            *baseline.warnings,
            *analysis.warnings,
            *validator_warnings,
        ]
    )

    return baseline.model_copy(
        update={
            "overall_match_score": overall_score,
            "required_skills_score": required_score,
            "preferred_skills_score": preferred_score,
            "technology_score": technology_score,
            "keyword_score": keyword_score,
            "responsibility_score": (responsibility_score),
            "matched_required_skills": (matched_required),
            "missing_required_skills": (missing_required),
            "matched_preferred_skills": (matched_preferred),
            "missing_preferred_skills": (missing_preferred),
            "matched_technologies": (matched_technologies),
            "missing_technologies": (missing_technologies),
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "responsibility_alignment": (responsibilities),
            "strengths": _deduplicate(
                [
                    *baseline.strengths,
                    *analysis.strengths,
                ]
            ),
            "weaknesses": _deduplicate(
                [
                    *baseline.weaknesses,
                    *analysis.weaknesses,
                ]
            ),
            "resume_evidence": evidence,
            "warnings": warnings,
            "scoring_breakdown": breakdown,
            "metadata": metadata,
        }
    )


def _fallback_result(
    baseline: ResumeJobMatchResult,
) -> ResumeJobMatchResult:
    warning = (
        "AI semantic matching was unavailable or "
        "invalid. The deterministic matching result "
        "was used."
    )

    metadata = baseline.metadata.model_copy(
        update={
            "engine_name": ("deterministic_resume_matching_fallback"),
            "engine_version": _AGENT_VERSION,
            "deterministic": True,
        }
    )

    return baseline.model_copy(
        update={
            "warnings": _deduplicate(
                [
                    *baseline.warnings,
                    warning,
                ]
            ),
            "metadata": metadata,
        }
    )


def _build_unavailable_runnable(
    message: str,
) -> ResumeMatchingRunnable:
    async def unavailable_model(
        _: dict[str, Any],
    ) -> SemanticResumeMatchingAnalysis:
        raise AgentConfigurationError(message)

    return cast(
        ResumeMatchingRunnable,
        RunnableLambda(unavailable_model),
    )


def _create_default_runnable() -> ResumeMatchingRunnable:
    try:
        model = create_chat_model()
    except AgentConfigurationError as exc:
        return _build_unavailable_runnable(str(exc))

    return build_resume_matching_runnable(model)


def build_resume_matching_workflow(
    runnable: ResumeMatchingRunnable,
    *,
    use_checkpointer: bool = True,
) -> Any:
    """Build the Resume Matching LangGraph workflow."""

    async def create_baseline(
        state: ResumeMatchingAgentState,
    ) -> dict[str, Any]:
        request = state["request"]

        try:
            baseline = match_resume_to_job(
                resume=request.resume,
                job_description=(request.job_description),
                resume_raw_text=(request.resume_raw_text),
                candidate_experience_years=(request.candidate_experience_years),
            )

            return {
                "baseline_result": baseline,
                "status": "analyzing",
                "last_error": None,
            }
        except Exception as exc:
            return {
                "baseline_result": None,
                "status": "failed",
                "last_error": (f"Deterministic baseline matching failed: {exc}"),
            }

    async def analyze(
        state: ResumeMatchingAgentState,
    ) -> dict[str, Any]:
        baseline = state.get("baseline_result")

        if baseline is None:
            return {
                "status": "failed",
                "last_error": ("Baseline result is unavailable."),
            }

        attempt_count = (
            state.get(
                "attempt_count",
                0,
            )
            + 1
        )

        agent_input = ResumeMatchingAgentInput(
            request=state["request"],
            baseline_result=baseline,
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
        state: ResumeMatchingAgentState,
    ) -> dict[str, Any]:
        result = state.get("agent_result")
        baseline = state.get("baseline_result")

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

        validation = validate_semantic_match_output(
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

        if validation.is_valid and baseline:
            final_result = _merge_results(
                state["request"],
                baseline,
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
            "validation_errors": validation.errors,
            "warnings": combined_warnings,
            "status": ("retrying" if attempt_count < max_attempts else "failed"),
        }

    async def fallback(
        state: ResumeMatchingAgentState,
    ) -> dict[str, Any]:
        baseline = state.get("baseline_result")

        if baseline is None:
            return {
                "final_result": None,
                "status": "failed",
                "last_error": ("AI matching and deterministic matching both failed."),
            }

        result = _fallback_result(baseline)

        return {
            "final_result": result,
            "warnings": list(result.warnings),
            "status": "completed_with_fallback",
        }

    async def reject(
        state: ResumeMatchingAgentState,
    ) -> dict[str, Any]:
        return {
            "status": "failed",
            "last_error": state.get("last_error"),
        }

    async def finalize(
        state: ResumeMatchingAgentState,
    ) -> dict[str, Any]:
        return {
            "status": state.get(
                "status",
                "completed",
            )
        }

    def route_after_baseline(
        state: ResumeMatchingAgentState,
    ) -> Literal["analyze", "reject"]:
        if state.get("status") == "failed" or state.get("baseline_result") is None:
            return "reject"

        return "analyze"

    def route_after_validation(
        state: ResumeMatchingAgentState,
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

    builder = StateGraph(ResumeMatchingAgentState)

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


async def run_resume_matching_workflow(
    *,
    request: ResumeJobMatchRequest,
    runnable: ResumeMatchingRunnable | None = None,
    max_attempts: int = 2,
    thread_id: str | None = None,
) -> ResumeMatchingAgentWorkflowResult:
    """Execute the Resume Matching AI workflow."""

    selected_runnable = runnable if runnable is not None else _create_default_runnable()

    graph = build_resume_matching_workflow(selected_runnable)

    initial_state: ResumeMatchingAgentState = {
        "request": request,
        "baseline_result": None,
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
        raise AgentExecutionError("Resume Matching Agent returned invalid workflow state.")

    return ResumeMatchingAgentWorkflowResult(
        status=raw_result.get(
            "status",
            "failed",
        ),
        match_result=raw_result.get("final_result"),
        semantic_analysis=raw_result.get("agent_result"),
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
