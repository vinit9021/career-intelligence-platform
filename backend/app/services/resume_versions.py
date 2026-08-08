"""Business logic for Resume Version Manager."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from app.models.resume_version import (
    ResumeVersion,
    ResumeVersionSubmission,
)
from app.repositories.resume_versions import (
    ResumeVersionRepositoryProtocol,
)
from app.schemas.resume_version import (
    ResumeSubmissionCreate,
    ResumeSubmissionRead,
    ResumeVariant,
    ResumeVersionCreate,
    ResumeVersionHistory,
    ResumeVersionRead,
)


class ResumeVersionNotFoundError(Exception):
    """Raised when a resume version does not exist."""


class ResumeVersionManagerService:
    """Manages resume variants and history."""

    def __init__(
        self,
        repository: ResumeVersionRepositoryProtocol,
    ) -> None:
        self.repository = repository

    async def create_version(
        self,
        request: ResumeVersionCreate,
    ) -> ResumeVersionRead:
        """Create the next version of a variant."""

        version_number = await self.repository.next_version_number(
            user_id=request.user_id,
            variant=request.variant,
        )

        now = datetime.now(UTC)

        version = ResumeVersion(
            id=uuid4(),
            user_id=request.user_id,
            source_resume_id=(request.source_resume_id),
            variant=request.variant,
            version_number=version_number,
            content=request.content.model_dump(mode="json"),
            optimization_snapshot=(request.optimization_snapshot),
            ats_score=request.ats_score,
            notes=request.notes,
            is_active=request.set_active,
            created_at=now,
            updated_at=now,
        )

        try:
            if request.set_active:
                await self.repository.clear_active_variant(
                    user_id=request.user_id,
                    variant=request.variant,
                )

            stored = await self.repository.add_version(version)

            await self.repository.commit()

        except Exception:
            await self.repository.rollback()
            raise

        return ResumeVersionRead.model_validate(stored)

    async def list_history(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> ResumeVersionHistory:
        """Return all versions newest-first."""

        versions = await self.repository.list_versions(
            user_id=user_id,
            variant=variant,
        )

        return ResumeVersionHistory(
            user_id=user_id,
            variant=variant,
            versions=[ResumeVersionRead.model_validate(version) for version in versions],
        )

    async def activate_version(
        self,
        *,
        user_id: UUID,
        version_id: UUID,
    ) -> ResumeVersionRead:
        """Make one version active for its variant."""

        version = await self.repository.get_version(
            user_id=user_id,
            version_id=version_id,
        )

        if version is None:
            raise ResumeVersionNotFoundError("Resume version was not found.")

        try:
            await self.repository.clear_active_variant(
                user_id=user_id,
                variant=cast(
                    ResumeVariant,
                    version.variant,
                ),
            )

            version.is_active = True
            version.updated_at = datetime.now(UTC)

            await self.repository.commit()

        except Exception:
            await self.repository.rollback()
            raise

        return ResumeVersionRead.model_validate(version)

    async def record_submission(
        self,
        request: ResumeSubmissionCreate,
    ) -> ResumeSubmissionRead:
        """Record which version was submitted."""

        version = await self.repository.get_version(
            user_id=request.user_id,
            version_id=request.resume_version_id,
        )

        if version is None:
            raise ResumeVersionNotFoundError("Resume version was not found.")

        submission = ResumeVersionSubmission(
            id=uuid4(),
            resume_version_id=version.id,
            application_reference=(request.application_reference),
            notes=request.notes,
            submitted_at=datetime.now(UTC),
        )

        try:
            stored = await self.repository.add_submission(submission)

            await self.repository.commit()

        except Exception:
            await self.repository.rollback()
            raise

        return ResumeSubmissionRead.model_validate(stored)

    async def list_submissions(
        self,
        *,
        user_id: UUID,
        version_id: UUID,
    ) -> list[ResumeSubmissionRead]:
        """Return submission history for a version."""

        version = await self.repository.get_version(
            user_id=user_id,
            version_id=version_id,
        )

        if version is None:
            raise ResumeVersionNotFoundError("Resume version was not found.")

        submissions = await self.repository.list_submissions(resume_version_id=version.id)

        return [ResumeSubmissionRead.model_validate(submission) for submission in submissions]

    async def get_submitted_version(
        self,
        *,
        user_id: UUID,
        application_reference: str,
    ) -> ResumeVersionRead | None:
        """Return version used for an application."""

        submission = await self.repository.get_submission_for_application(
            user_id=user_id,
            application_reference=(application_reference),
        )

        if submission is None:
            return None

        version = await self.repository.get_version(
            user_id=user_id,
            version_id=(submission.resume_version_id),
        )

        if version is None:
            return None

        return ResumeVersionRead.model_validate(version)
