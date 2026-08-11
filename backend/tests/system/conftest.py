"""Shared fixtures for Day 21 system tests."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel, Field

from app.memory.manager import MemoryManager
from app.memory.store import InMemoryMemoryStore
from app.orchestration.real_agents import RealAgentWorkflows
from app.prompts.management import get_default_prompt_manager
from app.tool_calling.runtime import build_default_tool_runtime
from app.workflow_execution.history import InMemoryWorkflowHistory
from app.workflow_execution.service import WorkflowExecutionService


class SystemAgentResult(BaseModel):
    """Generic result used by system-test agents."""

    status: str = "completed"

    resume: Any = None

    job_description: Any = None

    match_result: Any = None

    optimization: Any = None

    skill_gap: Any = None

    cover_letter: Any = None

    warnings: list[str] = Field(default_factory=list)


def build_success_workflows(
    calls: list[str],
) -> RealAgentWorkflows:
    """Build deterministic workflows for system testing."""

    async def resume_parser(
        *,
        text: str,
    ) -> SystemAgentResult:
        calls.append("resume_parser")

        assert text

        return SystemAgentResult(
            resume={
                "summary": ("Backend engineer"),
                "skills": [
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                ],
            }
        )

    async def jd_analyzer(
        *,
        text: str,
    ) -> SystemAgentResult:
        calls.append("job_description_analyzer")

        assert text

        return SystemAgentResult(
            job_description={
                "job_title": ("Backend Engineer"),
                "company": ("Example Company"),
                "required_skills": [
                    "Python",
                    "FastAPI",
                ],
                "preferred_skills": [
                    "Docker",
                ],
            }
        )

    async def resume_matching(
        *,
        resume: dict[str, Any],
        job_description: dict[str, Any],
        resume_raw_text: str,
    ) -> SystemAgentResult:
        calls.append("resume_matching")

        assert resume["skills"]

        assert job_description["required_skills"]

        assert resume_raw_text

        return SystemAgentResult(
            match_result={
                "overall_match_score": 88,
                "matched_skills": [
                    "Python",
                    "FastAPI",
                ],
                "missing_skills": [
                    "Docker",
                ],
            }
        )

    async def ats_optimization(
        *,
        resume: dict[str, Any],
        job_description: dict[str, Any],
        match_result: dict[str, Any],
        resume_raw_text: str,
        max_bullet_rewrites: int = 5,
    ) -> SystemAgentResult:
        calls.append("ats_optimization")

        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert max_bullet_rewrites > 0

        return SystemAgentResult(
            optimization={
                "ats_score": 91,
                "missing_keywords": [
                    "Docker",
                ],
            }
        )

    async def skill_gap(
        *,
        resume: dict[str, Any],
        job_description: dict[str, Any],
        match_result: dict[str, Any],
        resume_raw_text: str,
        max_roadmap_steps: int = 8,
        max_mini_projects: int = 3,
    ) -> SystemAgentResult:
        calls.append("skill_gap")

        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert max_roadmap_steps > 0
        assert max_mini_projects > 0

        return SystemAgentResult(
            skill_gap={
                "gaps": [
                    {
                        "skill": "Docker",
                        "priority": "high",
                    }
                ],
            }
        )

    async def cover_letter(
        *,
        resume: dict[str, Any],
        job_description: dict[str, Any],
        match_result: dict[str, Any],
        resume_raw_text: str,
        candidate_name: str | None = None,
        company_context: str | None = None,
        tone: str = "professional",
        max_words: int = 300,
    ) -> SystemAgentResult:
        calls.append("cover_letter")

        assert resume
        assert job_description
        assert match_result
        assert resume_raw_text
        assert tone
        assert max_words > 0

        del candidate_name
        del company_context

        return SystemAgentResult(
            cover_letter={
                "full_text": ("Dear Hiring Team, I am interested in the Backend Engineer role."),
            }
        )

    return RealAgentWorkflows(
        resume_parser=resume_parser,
        job_description_analyzer=(jd_analyzer),
        resume_matching=resume_matching,
        ats_optimization=(ats_optimization),
        skill_gap=skill_gap,
        cover_letter=cover_letter,
    )


def build_system_service(
    workflows: RealAgentWorkflows,
    *,
    memory: MemoryManager | None = None,
    history: InMemoryWorkflowHistory | None = None,
) -> WorkflowExecutionService:
    """Build fully integrated test execution service."""

    selected_memory = memory if memory is not None else MemoryManager(InMemoryMemoryStore())

    selected_history = history if history is not None else InMemoryWorkflowHistory()

    return WorkflowExecutionService(
        memory=selected_memory,
        history=selected_history,
        prompt_manager=(get_default_prompt_manager()),
        tool_runtime=(build_default_tool_runtime()),
        workflows=workflows,
    )


@pytest.fixture
def system_calls() -> list[str]:
    """Track real pipeline execution order."""

    return []


@pytest.fixture
def system_memory() -> MemoryManager:
    """Create isolated system-test memory."""

    return MemoryManager(InMemoryMemoryStore())


@pytest.fixture
def system_history() -> InMemoryWorkflowHistory:
    """Create isolated workflow history."""

    return InMemoryWorkflowHistory()


@pytest.fixture
def system_service(
    system_calls: list[str],
    system_memory: MemoryManager,
    system_history: InMemoryWorkflowHistory,
) -> WorkflowExecutionService:
    """Create complete Day 21 test service."""

    return build_system_service(
        build_success_workflows(system_calls),
        memory=system_memory,
        history=system_history,
    )
