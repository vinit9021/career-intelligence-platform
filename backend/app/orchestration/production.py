"""Production entry point for real agent orchestration."""

from __future__ import annotations

from typing import Any

from app.orchestration.graph import (
    run_career_workflow,
)
from app.orchestration.real_agents import (
    RealAgentWorkflows,
    build_real_agent_registry,
    load_real_agent_workflows,
)
from app.orchestration.state import (
    CORE_PIPELINE_ORDER,
    AgentNodeName,
    CareerWorkflowRequest,
    CareerWorkflowResult,
)


async def run_real_career_workflow(
    *,
    resume_raw_text: str,
    job_description_text: str,
    workflows: RealAgentWorkflows | None = None,
    enabled_nodes: list[AgentNodeName] | None = None,
    extra_context: dict[
        str,
        Any,
    ]
    | None = None,
    max_retries: int = 1,
    include_resume_version_manager: bool = False,
    thread_id: str | None = None,
) -> CareerWorkflowResult:
    """Execute real Career Intelligence agents."""

    selected_workflows = (
        workflows
        if workflows is not None
        else load_real_agent_workflows(
            include_resume_version_manager=(include_resume_version_manager)
        )
    )

    safe_extra_context = dict(extra_context or {})

    # Infrastructure objects cannot live inside
    # LangGraph checkpoint state.
    resume_version_agent = safe_extra_context.pop(
        "resume_version_agent",
        None,
    )

    registry = build_real_agent_registry(
        selected_workflows,
        include_resume_version_manager=(include_resume_version_manager),
        resume_version_agent=(resume_version_agent),
    )

    nodes = enabled_nodes if enabled_nodes is not None else list(CORE_PIPELINE_ORDER)

    context: dict[str, Any] = {
        "resume_raw_text": resume_raw_text,
        "job_description_text": (job_description_text),
    }

    context.update(safe_extra_context)

    request = CareerWorkflowRequest(
        enabled_nodes=nodes,
        initial_context=context,
    )

    return await run_career_workflow(
        registry=registry,
        request=request,
        max_retries=max_retries,
        thread_id=thread_id,
    )
