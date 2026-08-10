"""Additional coverage for Resume Version repository."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_version import (
    ResumeVersion,
    ResumeVersionSubmission,
)
from app.repositories.resume_versions import (
    ResumeVersionRepository,
)


def build_repository() -> tuple[Any, ResumeVersionRepository]:
    session: Any = MagicMock()

    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    repository = ResumeVersionRepository(
        cast(
            AsyncSession,
            session,
        )
    )

    return session, repository


@pytest.mark.asyncio
async def test_next_version_number() -> None:
    session, repository = build_repository()

    result: Any = MagicMock()

    result.scalar_one.return_value = 3

    session.execute.return_value = result

    number = await repository.next_version_number(
        user_id=uuid4(),
        variant="backend",
    )

    assert number == 4

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_version() -> None:
    session, repository = build_repository()

    version = cast(
        ResumeVersion,
        object(),
    )

    result = await repository.add_version(version)

    assert result is version

    session.add.assert_called_once_with(version)

    session.flush.assert_awaited_once()

    session.refresh.assert_awaited_once_with(version)


@pytest.mark.asyncio
async def test_get_version() -> None:
    session, repository = build_repository()

    version = cast(
        ResumeVersion,
        object(),
    )

    result_mock: Any = MagicMock()

    result_mock.scalar_one_or_none.return_value = version

    session.execute.return_value = result_mock

    result = await repository.get_version(
        user_id=uuid4(),
        version_id=uuid4(),
    )

    assert result is version


@pytest.mark.asyncio
async def test_list_versions() -> None:
    session, repository = build_repository()

    version = cast(
        ResumeVersion,
        object(),
    )

    result_mock: Any = MagicMock()

    result_mock.scalars.return_value.all.return_value = [version]

    session.execute.return_value = result_mock

    result = await repository.list_versions(
        user_id=uuid4(),
        variant="ai",
    )

    assert list(result) == [version]


@pytest.mark.asyncio
async def test_clear_active_variant() -> None:
    session, repository = build_repository()

    await repository.clear_active_variant(
        user_id=uuid4(),
        variant="ml",
    )

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_submission() -> None:
    session, repository = build_repository()

    submission = cast(
        ResumeVersionSubmission,
        object(),
    )

    result = await repository.add_submission(submission)

    assert result is submission

    session.add.assert_called_once_with(submission)

    session.flush.assert_awaited_once()

    session.refresh.assert_awaited_once_with(submission)


@pytest.mark.asyncio
async def test_list_submissions() -> None:
    session, repository = build_repository()

    submission = cast(
        ResumeVersionSubmission,
        object(),
    )

    result_mock: Any = MagicMock()

    result_mock.scalars.return_value.all.return_value = [submission]

    session.execute.return_value = result_mock

    result = await repository.list_submissions(resume_version_id=uuid4())

    assert list(result) == [submission]


@pytest.mark.asyncio
async def test_get_submission_for_application() -> None:
    session, repository = build_repository()

    submission = cast(
        ResumeVersionSubmission,
        object(),
    )

    result_mock: Any = MagicMock()

    result_mock.scalar_one_or_none.return_value = submission

    session.execute.return_value = result_mock

    result = await repository.get_submission_for_application(
        user_id=uuid4(),
        application_reference=("application-1"),
    )

    assert result is submission


@pytest.mark.asyncio
async def test_commit_and_rollback() -> None:
    session, repository = build_repository()

    await repository.commit()

    await repository.rollback()

    session.commit.assert_awaited_once()

    session.rollback.assert_awaited_once()
