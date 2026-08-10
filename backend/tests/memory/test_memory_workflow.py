"""Tests for memory-aware LangGraph orchestration."""

from typing import Any

import pytest
from pydantic import BaseModel

from app.memory.manager import (
    MemoryManager,
)
from app.memory.store import (
    InMemoryMemoryStore,
)
from app.memory.workflow import (
    run_memory_aware_career_workflow,
)
from app.orchestration.real_agents import (
    RealAgentWorkflows,
)


class Result(BaseModel):
    status: str = "completed"

    resume: Any = None

    warnings: list[str] = []


@pytest.mark.asyncio
async def test_workflow_result_is_remembered() -> None:
    memory = MemoryManager(InMemoryMemoryStore())

    async def resume_parser(
        *,
        text: str,
    ) -> Result:
        assert text

        return Result(resume={"skills": ["Python"]})

    async def unused(
        **_: Any,
    ) -> Result:
        return Result()

    workflows = RealAgentWorkflows(
        resume_parser=resume_parser,
        job_description_analyzer=unused,
        resume_matching=unused,
        ats_optimization=unused,
        skill_gap=unused,
        cover_letter=unused,
    )

    result = await run_memory_aware_career_workflow(
        memory=memory,
        user_id="u1",
        session_id="session-1",
        resume_raw_text=("Python developer"),
        job_description_text=("Backend Engineer"),
        workflows=workflows,
        enabled_nodes=["resume_parser"],
    )

    assert result.status == "completed"

    saved = await memory.recall(
        user_id="u1",
        scope="short_term",
        namespace="workflow",
        key="last_result",
        session_id="session-1",
    )

    assert saved is not None

    assert saved["status"] == "completed"


@pytest.mark.asyncio
async def test_long_term_memory_is_available() -> None:
    memory = MemoryManager(InMemoryMemoryStore())

    await memory.remember(
        user_id="u1",
        scope="long_term",
        namespace="career_goals",
        key="target_role",
        value="AI Engineer",
    )

    context = await memory.build_context(
        user_id="u1",
        session_id="session-1",
    )

    assert context["long_term"]["career_goals"]["target_role"] == "AI Engineer"
