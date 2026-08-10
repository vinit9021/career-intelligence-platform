"""Tests for end-to-end workflow execution."""

import pytest

from app.memory.manager import (
    MemoryManager,
)
from app.workflow_execution.history import (
    InMemoryWorkflowHistory,
)
from app.workflow_execution.models import (
    WorkflowExecutionRequest,
)
from app.workflow_execution.service import (
    WorkflowExecutionService,
)


@pytest.mark.asyncio
async def test_executes_full_agent_pipeline(
    service: WorkflowExecutionService,
    calls: list[str],
) -> None:
    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="session-1",
            resume_raw_text=("Python FastAPI developer"),
            job_description_text=("Backend Engineer requiring Python"),
        )
    )

    assert result.status == "completed"

    assert calls == [
        "resume_parser",
        "job_description_analyzer",
        "resume_matching",
        "ats_optimization",
        "skill_gap",
        "cover_letter",
    ]

    assert all(step.status == "completed" for step in result.steps)

    assert result.outputs["resume_matching"]["overall_match_score"] == 90


@pytest.mark.asyncio
async def test_supports_partial_execution(
    service: WorkflowExecutionService,
    calls: list[str],
) -> None:
    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="session-2",
            resume_raw_text=("Python developer"),
            job_description_text=("Backend Engineer"),
            enabled_nodes=[
                "resume_parser",
                "job_description_analyzer",
                "resume_matching",
            ],
        )
    )

    assert result.status == "completed"

    assert calls == [
        "resume_parser",
        "job_description_analyzer",
        "resume_matching",
    ]

    assert len(result.steps) == 3


@pytest.mark.asyncio
async def test_dependency_failure_is_structured(
    service: WorkflowExecutionService,
) -> None:
    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="session-3",
            resume_raw_text="Resume",
            job_description_text="JD",
            enabled_nodes=["resume_matching"],
            max_retries=0,
        )
    )

    assert result.status == "failed"

    assert result.failed_node == "resume_matching"

    assert result.steps[0].status == "failed"

    assert result.errors


@pytest.mark.asyncio
async def test_workflow_result_is_saved_to_memory(
    service: WorkflowExecutionService,
    memory: MemoryManager,
) -> None:
    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="memory-session",
            resume_raw_text="Python",
            job_description_text="Backend",
            enabled_nodes=["resume_parser"],
        )
    )

    assert result.status == "completed"

    saved = await memory.recall(
        user_id="u1",
        scope="short_term",
        namespace="workflow",
        key="last_result",
        session_id="memory-session",
    )

    assert saved is not None

    assert saved["status"] == "completed"


@pytest.mark.asyncio
async def test_execution_history_is_saved(
    service: WorkflowExecutionService,
    history: InMemoryWorkflowHistory,
) -> None:
    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="history-session",
            resume_raw_text="Python",
            job_description_text="Backend",
            enabled_nodes=["resume_parser"],
        )
    )

    record = await history.get(result.execution_id)

    assert record is not None

    assert record.status == "completed"

    assert record.output_keys == ["resume_parser"]


@pytest.mark.asyncio
async def test_execution_contains_prompt_metadata(
    service: WorkflowExecutionService,
) -> None:
    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="prompt-session",
            resume_raw_text="Python",
            job_description_text="Backend",
            enabled_nodes=["resume_parser"],
        )
    )

    prompts = result.metadata["prompt_versions"]

    assert prompts["resume_parser"]["version"] == "1.0.0"

    assert len(prompts["resume_parser"]["checksum"]) == 64


@pytest.mark.asyncio
async def test_execution_contains_tool_metadata(
    service: WorkflowExecutionService,
) -> None:
    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="tool-session",
            resume_raw_text="Python",
            job_description_text="Backend",
            enabled_nodes=[
                "resume_parser",
                "job_description_analyzer",
                "resume_matching",
            ],
        )
    )

    allowed = result.metadata["allowed_tools"]

    assert allowed["resume_parser"] == ["evidence_lookup"]

    assert set(allowed["resume_matching"]) == {
        "evidence_lookup",
        "keyword_overlap",
    }


@pytest.mark.asyncio
async def test_missing_version_manager_dependency_fails(
    service: WorkflowExecutionService,
) -> None:
    result = await service.execute(
        WorkflowExecutionRequest(
            user_id="u1",
            session_id="version-session",
            resume_raw_text="Resume",
            job_description_text="JD",
            enabled_nodes=["resume_version_manager"],
            include_resume_version_manager=True,
        )
    )

    assert result.status == "failed"

    assert result.errors

    assert "resume_version_agent" in result.errors[0]
