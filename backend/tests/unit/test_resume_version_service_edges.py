"""Edge-case coverage for Resume Version service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.models.resume_version import (
    ResumeVersion,
    ResumeVersionSubmission,
)
from app.repositories.resume_versions import (
    ResumeVersionRepositoryProtocol,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)
from app.schemas.resume_version import (
    ResumeSubmissionCreate,
    ResumeVersionCreate,
)
from app.services.resume_versions import (
    ResumeVersionManagerService,
    ResumeVersionNotFoundError,
)


def build_resume() -> ResumeStructuredContent:
    return ResumeStructuredContent.model_validate(
        {
            "summary": "Backend engineer",
            "skills": [
                "Python",
                "FastAPI",
            ],
            "experience": ["Built APIs."],
            "education": [],
            "projects": [],
            "certifications": [],
        }
    )


def build_version(
    user_id: UUID,
) -> ResumeVersion:
    now = datetime.now(UTC)

    return ResumeVersion(
        id=uuid4(),
        user_id=user_id,
        source_resume_id=None,
        variant="backend",
        version_number=1,
        content=(build_resume().model_dump(mode="json")),
        optimization_snapshot=None,
        ats_score=None,
        notes=None,
        is_active=False,
        created_at=now,
        updated_at=now,
    )


def build_submission(
    version_id: UUID,
) -> ResumeVersionSubmission:
    return ResumeVersionSubmission(
        id=uuid4(),
        resume_version_id=version_id,
        application_reference=("application-1"),
        notes=None,
        submitted_at=datetime.now(UTC),
    )


def build_service() -> tuple[Any, ResumeVersionManagerService]:
    repository: Any = MagicMock()

    repository.next_version_number = AsyncMock(return_value=1)

    repository.clear_active_variant = AsyncMock()

    repository.add_version = AsyncMock()

    repository.get_version = AsyncMock()

    repository.list_versions = AsyncMock(return_value=[])

    repository.add_submission = AsyncMock()

    repository.list_submissions = AsyncMock(return_value=[])

    repository.get_submission_for_application = AsyncMock()

    repository.commit = AsyncMock()

    repository.rollback = AsyncMock()

    service = ResumeVersionManagerService(
        cast(
            ResumeVersionRepositoryProtocol,
            repository,
        )
    )

    return repository, service


@pytest.mark.asyncio
async def test_create_inactive_version_skips_clear() -> None:
    repository, service = build_service()

    user_id = uuid4()

    repository.add_version.side_effect = lambda version: version

    result = await service.create_version(
        ResumeVersionCreate(
            user_id=user_id,
            variant="backend",
            content=build_resume(),
            set_active=False,
        )
    )

    assert result.is_active is False

    repository.clear_active_variant.assert_not_awaited()

    repository.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_version_rolls_back() -> None:
    repository, service = build_service()

    repository.add_version.side_effect = RuntimeError("database failure")

    with pytest.raises(
        RuntimeError,
        match="database failure",
    ):
        await service.create_version(
            ResumeVersionCreate(
                user_id=uuid4(),
                variant="backend",
                content=build_resume(),
            )
        )

    repository.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_activate_missing_version() -> None:
    repository, service = build_service()

    repository.get_version.return_value = None

    with pytest.raises(ResumeVersionNotFoundError):
        await service.activate_version(
            user_id=uuid4(),
            version_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_activate_rolls_back_on_commit_error() -> None:
    repository, service = build_service()

    user_id = uuid4()

    version = build_version(user_id)

    repository.get_version.return_value = version

    repository.commit.side_effect = RuntimeError("commit failure")

    with pytest.raises(
        RuntimeError,
        match="commit failure",
    ):
        await service.activate_version(
            user_id=user_id,
            version_id=version.id,
        )

    repository.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_record_submission_missing_version() -> None:
    repository, service = build_service()

    repository.get_version.return_value = None

    with pytest.raises(ResumeVersionNotFoundError):
        await service.record_submission(
            ResumeSubmissionCreate(
                user_id=uuid4(),
                resume_version_id=uuid4(),
                application_reference=("application-1"),
            )
        )


@pytest.mark.asyncio
async def test_record_submission_rolls_back() -> None:
    repository, service = build_service()

    user_id = uuid4()

    version = build_version(user_id)

    repository.get_version.return_value = version

    repository.add_submission.side_effect = RuntimeError("submission failure")

    with pytest.raises(
        RuntimeError,
        match="submission failure",
    ):
        await service.record_submission(
            ResumeSubmissionCreate(
                user_id=user_id,
                resume_version_id=(version.id),
                application_reference=("application-1"),
            )
        )

    repository.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_submissions_missing_version() -> None:
    repository, service = build_service()

    repository.get_version.return_value = None

    with pytest.raises(ResumeVersionNotFoundError):
        await service.list_submissions(
            user_id=uuid4(),
            version_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_list_submissions_success() -> None:
    repository, service = build_service()

    user_id = uuid4()

    version = build_version(user_id)

    submission = build_submission(version.id)

    repository.get_version.return_value = version

    repository.list_submissions.return_value = [submission]

    result = await service.list_submissions(
        user_id=user_id,
        version_id=version.id,
    )

    assert len(result) == 1

    assert result[0].resume_version_id == version.id


@pytest.mark.asyncio
async def test_get_submitted_version_without_submission() -> None:
    repository, service = build_service()

    repository.get_submission_for_application.return_value = None

    result = await service.get_submitted_version(
        user_id=uuid4(),
        application_reference=("missing"),
    )

    assert result is None


@pytest.mark.asyncio
async def test_get_submitted_version_missing_resume() -> None:
    repository, service = build_service()

    version_id = uuid4()

    repository.get_submission_for_application.return_value = build_submission(version_id)

    repository.get_version.return_value = None

    result = await service.get_submitted_version(
        user_id=uuid4(),
        application_reference=("application-1"),
    )

    assert result is None
