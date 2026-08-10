"""Shared fixtures for workflow execution tests."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, Field

from app.memory.manager import (
    MemoryManager,
)
from app.memory.store import (
    InMemoryMemoryStore,
)
from app.orchestration.real_agents import (
    RealAgentWorkflows,
)
from app.prompts.management import (
    get_default_prompt_manager,
)
from app.tool_calling.runtime import (
    build_default_tool_runtime,
)
from app.workflow_execution.history import (
    InMemoryWorkflowHistory,
)
from app.workflow_execution.service import (
    WorkflowExecutionService,
)


class AgentResult(BaseModel):
    status: str = "completed"

    resume: Any = None

    job_description: Any = None

    match_result: Any = None

    optimization: Any = None

    skill_gap: Any = None

    cover_letter: Any = None

    warnings: list[str] = Field(default_factory=list)


def fake_workflows(
    calls: list[str],
) -> RealAgentWorkflows:
    async def resume_parser(
        *,
        text: str,
    ) -> AgentResult:
        calls.append("resume_parser")

        assert text

        return AgentResult(
            resume={
                "skills": [
                    "Python",
                    "FastAPI",
                ]
            }
        )

    async def jd_analyzer(
        *,
        text: str,
    ) -> AgentResult:
        calls.append("job_description_analyzer")

        assert text

        return AgentResult(
            job_description={
                "job_title": ("Backend Engineer"),
                "required_skills": [
                    "Python",
                ],
            }
        )

    async def resume_matching(
        *,
        resume: dict[str, Any],
        job_description: dict[
            str,
            Any,
        ],
        resume_raw_text: str,
    ) -> AgentResult:
        calls.append("resume_matching")

        assert resume["skills"]
        assert job_description["job_title"]
        assert resume_raw_text

        return AgentResult(match_result={"overall_match_score": 90})

    async def ats(
        *,
        resume: dict[str, Any],
        job_description: dict[
            str,
            Any,
        ],
        match_result: dict[
            str,
            Any,
        ],
        resume_raw_text: str,
        max_bullet_rewrites: int = 5,
    ) -> AgentResult:
        calls.append("ats_optimization")

        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert max_bullet_rewrites > 0

        return AgentResult(optimization={"ats_score": 92})

    async def skill_gap(
        *,
        resume: dict[str, Any],
        job_description: dict[
            str,
            Any,
        ],
        match_result: dict[
            str,
            Any,
        ],
        resume_raw_text: str,
        max_roadmap_steps: int = 8,
        max_mini_projects: int = 3,
    ) -> AgentResult:
        calls.append("skill_gap")

        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert max_roadmap_steps > 0
        assert max_mini_projects > 0

        return AgentResult(skill_gap={"gaps": []})

    async def cover_letter(
        *,
        resume: dict[str, Any],
        job_description: dict[
            str,
            Any,
        ],
        match_result: dict[
            str,
            Any,
        ],
        resume_raw_text: str,
        candidate_name: str | None = None,
        company_context: str | None = None,
        tone: str = "professional",
        max_words: int = 300,
    ) -> AgentResult:
        calls.append("cover_letter")

        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert tone
        assert max_words > 0

        del candidate_name
        del company_context

        return AgentResult(cover_letter={"full_text": ("Dear Hiring Team")})

    return RealAgentWorkflows(
        resume_parser=resume_parser,
        job_description_analyzer=(jd_analyzer),
        resume_matching=resume_matching,
        ats_optimization=ats,
        skill_gap=skill_gap,
        cover_letter=cover_letter,
    )


@pytest.fixture
def calls() -> list[str]:
    return []


@pytest.fixture
def memory() -> MemoryManager:
    return MemoryManager(InMemoryMemoryStore())


@pytest.fixture
def history() -> InMemoryWorkflowHistory:
    return InMemoryWorkflowHistory()


@pytest.fixture
def service(
    calls: list[str],
    memory: MemoryManager,
    history: InMemoryWorkflowHistory,
) -> WorkflowExecutionService:
    return WorkflowExecutionService(
        memory=memory,
        history=history,
        prompt_manager=(get_default_prompt_manager()),
        tool_runtime=(build_default_tool_runtime()),
        workflows=fake_workflows(calls),
    )
