"""Tests for Resume Version Manager service."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID, uuid4

import pytest

from app.models.resume_version import (
    ResumeVersion,
    ResumeVersionSubmission,
)
from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)
from app.schemas.resume_version import (
    ResumeSubmissionCreate,
    ResumeVariant,
    ResumeVersionCreate,
)
from app.services.resume_versions import (
    ResumeVersionManagerService,
)


class FakeRepository:
    def __init__(self) -> None:
        self.versions: list[ResumeVersion] = []
        self.submissions: list[ResumeVersionSubmission] = []
        self.commit_count = 0
        self.rollback_count = 0

    async def next_version_number(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> int:
        numbers = [
            item.version_number
            for item in self.versions
            if (item.user_id == user_id and item.variant == variant)
        ]

        return max(numbers, default=0) + 1

    async def add_version(
        self,
        version: ResumeVersion,
    ) -> ResumeVersion:
        self.versions.append(version)
        return version

    async def get_version(
        self,
        *,
        user_id: UUID,
        version_id: UUID,
    ) -> ResumeVersion | None:
        return next(
            (item for item in self.versions if (item.user_id == user_id and item.id == version_id)),
            None,
        )

    async def list_versions(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> Sequence[ResumeVersion]:
        values = [
            item for item in self.versions if (item.user_id == user_id and item.variant == variant)
        ]

        return sorted(
            values,
            key=lambda item: item.version_number,
            reverse=True,
        )

    async def clear_active_variant(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> None:
        for item in self.versions:
            if item.user_id == user_id and item.variant == variant:
                item.is_active = False

    async def add_submission(
        self,
        submission: ResumeVersionSubmission,
    ) -> ResumeVersionSubmission:
        self.submissions.append(submission)
        return submission

    async def list_submissions(
        self,
        *,
        resume_version_id: UUID,
    ) -> Sequence[ResumeVersionSubmission]:
        return [item for item in self.submissions if (item.resume_version_id == resume_version_id)]

    async def get_submission_for_application(
        self,
        *,
        user_id: UUID,
        application_reference: str,
    ) -> ResumeVersionSubmission | None:
        version_ids = {item.id for item in self.versions if item.user_id == user_id}

        return next(
            (
                item
                for item in reversed(self.submissions)
                if (
                    item.resume_version_id in version_ids
                    and item.application_reference == application_reference
                )
            ),
            None,
        )

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


def build_resume() -> ResumeStructuredContent:
    return ResumeStructuredContent.model_validate(
        {
            "summary": "Backend engineer",
            "skills": [
                "Python",
                "FastAPI",
            ],
            "experience": ["Built backend APIs."],
            "education": [],
            "projects": [],
            "certifications": [],
        }
    )


@pytest.mark.asyncio
async def test_creates_sequential_versions() -> None:
    repository = FakeRepository()

    service = ResumeVersionManagerService(repository)

    user_id = uuid4()

    first = await service.create_version(
        ResumeVersionCreate(
            user_id=user_id,
            variant="backend",
            content=build_resume(),
        )
    )

    second = await service.create_version(
        ResumeVersionCreate(
            user_id=user_id,
            variant="backend",
            content=build_resume(),
        )
    )

    assert first.version_number == 1
    assert second.version_number == 2
    assert second.is_active is True
    assert repository.versions[0].is_active is False


@pytest.mark.asyncio
async def test_variants_have_independent_versions() -> None:
    repository = FakeRepository()

    service = ResumeVersionManagerService(repository)

    user_id = uuid4()

    backend = await service.create_version(
        ResumeVersionCreate(
            user_id=user_id,
            variant="backend",
            content=build_resume(),
        )
    )

    ai = await service.create_version(
        ResumeVersionCreate(
            user_id=user_id,
            variant="ai",
            content=build_resume(),
        )
    )

    assert backend.version_number == 1
    assert ai.version_number == 1


@pytest.mark.asyncio
async def test_activate_old_version() -> None:
    repository = FakeRepository()

    service = ResumeVersionManagerService(repository)

    user_id = uuid4()

    first = await service.create_version(
        ResumeVersionCreate(
            user_id=user_id,
            variant="ml",
            content=build_resume(),
        )
    )

    await service.create_version(
        ResumeVersionCreate(
            user_id=user_id,
            variant="ml",
            content=build_resume(),
        )
    )

    active = await service.activate_version(
        user_id=user_id,
        version_id=first.id,
    )

    assert active.is_active is True

    active_versions = [item for item in repository.versions if item.is_active]

    assert len(active_versions) == 1
    assert active_versions[0].id == first.id


@pytest.mark.asyncio
async def test_tracks_submitted_version() -> None:
    repository = FakeRepository()

    service = ResumeVersionManagerService(repository)

    user_id = uuid4()

    version = await service.create_version(
        ResumeVersionCreate(
            user_id=user_id,
            variant="full_stack",
            content=build_resume(),
        )
    )

    submission = await service.record_submission(
        ResumeSubmissionCreate(
            user_id=user_id,
            resume_version_id=(version.id),
            application_reference=("example-backend-001"),
        )
    )

    submitted_version = await service.get_submitted_version(
        user_id=user_id,
        application_reference=("example-backend-001"),
    )

    assert submission.resume_version_id == version.id

    assert submitted_version is not None
    assert submitted_version.id == version.id


@pytest.mark.asyncio
async def test_returns_variant_history() -> None:
    repository = FakeRepository()

    service = ResumeVersionManagerService(repository)

    user_id = uuid4()

    for _ in range(3):
        await service.create_version(
            ResumeVersionCreate(
                user_id=user_id,
                variant="ai",
                content=build_resume(),
            )
        )

    history = await service.list_history(
        user_id=user_id,
        variant="ai",
    )

    assert len(history.versions) == 3

    assert [item.version_number for item in history.versions] == [3, 2, 1]
