"""Tests for Resume Version Manager workflow."""

from uuid import uuid4

import pytest

from app.agents.resume_version_manager.agent import (
    ResumeVersionManagerAgent,
)
from app.schemas.resume_version import (
    ResumeSubmissionCreate,
    ResumeVersionCreate,
)
from app.services.resume_versions import (
    ResumeVersionManagerService,
)
from app.workflows.resume_version_manager import (
    ResumeVersionManagerRequest,
    run_resume_version_manager_workflow,
)
from tests.unit.test_resume_version_service import (
    FakeRepository,
    build_resume,
)


@pytest.mark.asyncio
async def test_workflow_creates_version() -> None:
    repository = FakeRepository()

    agent = ResumeVersionManagerAgent(ResumeVersionManagerService(repository))

    response = await run_resume_version_manager_workflow(
        agent=agent,
        request=ResumeVersionManagerRequest(
            operation="create",
            create_request=(
                ResumeVersionCreate(
                    user_id=uuid4(),
                    variant="backend",
                    content=build_resume(),
                )
            ),
        ),
    )

    assert response.status == "completed"
    assert response.version is not None
    assert response.version.version_number == 1


@pytest.mark.asyncio
async def test_workflow_tracks_submission() -> None:
    repository = FakeRepository()

    agent = ResumeVersionManagerAgent(ResumeVersionManagerService(repository))

    user_id = uuid4()

    version = await agent.create_variant(
        ResumeVersionCreate(
            user_id=user_id,
            variant="ml",
            content=build_resume(),
        )
    )

    response = await run_resume_version_manager_workflow(
        agent=agent,
        request=ResumeVersionManagerRequest(
            operation="submit",
            submission_request=(
                ResumeSubmissionCreate(
                    user_id=user_id,
                    resume_version_id=(version.id),
                    application_reference=("ml-role-001"),
                )
            ),
        ),
    )

    assert response.status == "completed"
    assert response.submission is not None
    assert response.submission.resume_version_id == version.id


@pytest.mark.asyncio
async def test_workflow_rejects_bad_command() -> None:
    repository = FakeRepository()

    agent = ResumeVersionManagerAgent(ResumeVersionManagerService(repository))

    response = await run_resume_version_manager_workflow(
        agent=agent,
        request=ResumeVersionManagerRequest(operation="activate"),
    )

    assert response.status == "failed"
    assert response.errors
