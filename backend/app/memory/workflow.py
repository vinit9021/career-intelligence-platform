"""Memory-aware wrapper around Career LangGraph orchestration."""

from __future__ import annotations

from typing import Any

from app.memory.manager import MemoryManager
from app.orchestration.production import (
    run_real_career_workflow,
)
from app.orchestration.real_agents import (
    RealAgentWorkflows,
)
from app.orchestration.state import (
    AgentNodeName,
    CareerWorkflowResult,
)


async def run_memory_aware_career_workflow(
    *,
    memory: MemoryManager,
    user_id: str,
    session_id: str,
    resume_raw_text: str,
    job_description_text: str,
    workflows: RealAgentWorkflows | None = None,
    enabled_nodes: (list[AgentNodeName] | None) = None,
    extra_context: (dict[str, Any] | None) = None,
    max_retries: int = 1,
    include_resume_version_manager: (bool) = False,
) -> CareerWorkflowResult:
    """Run orchestration with agent memory context."""

    memory_context = await memory.build_context(
        user_id=user_id,
        session_id=session_id,
    )

    context = dict(extra_context or {})

    context["memory"] = memory_context

    result = await run_real_career_workflow(
        resume_raw_text=(resume_raw_text),
        job_description_text=(job_description_text),
        workflows=workflows,
        enabled_nodes=enabled_nodes,
        extra_context=context,
        max_retries=max_retries,
        include_resume_version_manager=(include_resume_version_manager),
        thread_id=session_id,
    )

    await memory.remember(
        user_id=user_id,
        scope="short_term",
        namespace="workflow",
        key="last_result",
        value=result,
        session_id=session_id,
        source_agent="orchestration",
    )

    return result
