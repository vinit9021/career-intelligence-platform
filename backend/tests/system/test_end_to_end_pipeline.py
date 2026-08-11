"""End-to-end regression tests for the agentic pipeline."""

from __future__ import annotations

import pytest

from app.memory.manager import MemoryManager
from app.orchestration.state import CORE_PIPELINE_ORDER
from app.workflow_execution.history import InMemoryWorkflowHistory
from app.workflow_execution.models import WorkflowExecutionRequest
from app.workflow_execution.service import WorkflowExecutionService


@pytest.mark.asyncio
async def test_complete_agentic_pipeline(
    system_service: WorkflowExecutionService,
    system_calls: list[str],
) -> None:
    """All core agents execute in expected order."""

    result = await system_service.execute(
        WorkflowExecutionRequest(
            user_id="system-user",
            session_id=("system-session-1"),
            resume_raw_text=("Backend engineer with Python, FastAPI and PostgreSQL."),
            job_description_text=("Backend Engineer requiring Python, FastAPI and Docker."),
            extra_context={
                "candidate_name": "Candidate",
                "company_context": ("Example Company builds backend platforms."),
            },
        )
    )

    assert result.status == "completed"

    assert system_calls == list(CORE_PIPELINE_ORDER)

    assert [step.node for step in result.steps] == list(CORE_PIPELINE_ORDER)

    assert all(step.status == "completed" for step in result.steps)

    assert result.outputs["resume_matching"]["overall_match_score"] == 88

    assert result.outputs["ats_optimization"]["ats_score"] == 91

    assert result.outputs["skill_gap"]["gaps"][0]["skill"] == "Docker"

    assert "Backend Engineer" in result.outputs["cover_letter"]["full_text"]

    assert result.duration_ms >= 0

    assert result.errors == []


@pytest.mark.asyncio
async def test_pipeline_records_memory_and_history(
    system_service: WorkflowExecutionService,
    system_memory: MemoryManager,
    system_history: InMemoryWorkflowHistory,
) -> None:
    """Workflow result is available through memory and history."""

    request = WorkflowExecutionRequest(
        user_id="system-user",
        session_id=("system-session-2"),
        resume_raw_text=("Python backend developer."),
        job_description_text=("Backend Engineer requiring Python."),
        enabled_nodes=[
            "resume_parser",
            "job_description_analyzer",
            "resume_matching",
        ],
    )

    result = await system_service.execute(request)

    memory_result = await system_memory.recall(
        user_id=request.user_id,
        scope="short_term",
        namespace="workflow",
        key="last_result",
        session_id=(request.session_id),
    )

    assert memory_result is not None

    assert memory_result["status"] == "completed"

    history_result = await system_history.get(result.execution_id)

    assert history_result is not None

    assert history_result.status == "completed"

    assert history_result.output_keys == [
        "job_description_analyzer",
        "resume_matching",
        "resume_parser",
    ]


@pytest.mark.asyncio
async def test_workflow_metadata_integrations(
    system_service: WorkflowExecutionService,
) -> None:
    """Prompt and tool metadata are attached to execution."""

    result = await system_service.execute(
        WorkflowExecutionRequest(
            user_id="system-user",
            session_id=("metadata-session"),
            resume_raw_text="Python developer",
            job_description_text=("Backend Engineer"),
            enabled_nodes=[
                "resume_parser",
                "job_description_analyzer",
                "resume_matching",
            ],
        )
    )

    assert result.metadata["memory_enabled"] is True

    assert result.metadata["tool_calling_enabled"] is True

    prompt_versions = result.metadata["prompt_versions"]

    assert prompt_versions["resume_parser"]["version"] == "1.0.0"

    assert len(prompt_versions["resume_parser"]["checksum"]) == 64

    allowed_tools = result.metadata["allowed_tools"]

    assert allowed_tools["resume_parser"] == ["evidence_lookup"]

    assert set(allowed_tools["resume_matching"]) == {
        "evidence_lookup",
        "keyword_overlap",
    }
