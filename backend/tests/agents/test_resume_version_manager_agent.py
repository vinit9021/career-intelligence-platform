"""Tests for Resume Version Manager Agent."""

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
from tests.unit.test_resume_version_service import (
    FakeRepository,
    build_resume,
)


@pytest.mark.asyncio
async def test_agent_creates_variant() -> None:
    repository = FakeRepository()

    agent = ResumeVersionManagerAgent(ResumeVersionManagerService(repository))

    result = await agent.create_variant(
        ResumeVersionCreate(
            user_id=uuid4(),
            variant="backend",
            content=build_resume(),
        )
    )

    assert result.variant == "backend"
    assert result.version_number == 1


@pytest.mark.asyncio
async def test_agent_tracks_submission() -> None:
    repository = FakeRepository()

    agent = ResumeVersionManagerAgent(ResumeVersionManagerService(repository))

    user_id = uuid4()

    version = await agent.create_variant(
        ResumeVersionCreate(
            user_id=user_id,
            variant="ai",
            content=build_resume(),
        )
    )

    result = await agent.track_submission(
        ResumeSubmissionCreate(
            user_id=user_id,
            resume_version_id=version.id,
            application_reference="app-001",
        )
    )

    assert result.application_reference == ("app-001")
