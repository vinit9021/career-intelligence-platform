"""Repository for resume version persistence."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_version import (
    ResumeVersion,
    ResumeVersionSubmission,
)
from app.schemas.resume_version import ResumeVariant


class ResumeVersionRepositoryProtocol(Protocol):
    """Repository contract used by the service."""

    async def next_version_number(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> int: ...

    async def add_version(
        self,
        version: ResumeVersion,
    ) -> ResumeVersion: ...

    async def get_version(
        self,
        *,
        user_id: UUID,
        version_id: UUID,
    ) -> ResumeVersion | None: ...

    async def list_versions(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> Sequence[ResumeVersion]: ...

    async def clear_active_variant(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> None: ...

    async def add_submission(
        self,
        submission: ResumeVersionSubmission,
    ) -> ResumeVersionSubmission: ...

    async def list_submissions(
        self,
        *,
        resume_version_id: UUID,
    ) -> Sequence[ResumeVersionSubmission]: ...

    async def get_submission_for_application(
        self,
        *,
        user_id: UUID,
        application_reference: str,
    ) -> ResumeVersionSubmission | None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class ResumeVersionRepository:
    """SQLAlchemy implementation."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def next_version_number(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> int:
        statement = select(
            func.coalesce(
                func.max(ResumeVersion.version_number),
                0,
            )
        ).where(
            ResumeVersion.user_id == user_id,
            ResumeVersion.variant == variant,
        )

        result = await self.session.execute(statement)

        current = result.scalar_one()

        return int(current) + 1

    async def add_version(
        self,
        version: ResumeVersion,
    ) -> ResumeVersion:
        self.session.add(version)

        await self.session.flush()
        await self.session.refresh(version)

        return version

    async def get_version(
        self,
        *,
        user_id: UUID,
        version_id: UUID,
    ) -> ResumeVersion | None:
        statement = select(ResumeVersion).where(
            ResumeVersion.id == version_id,
            ResumeVersion.user_id == user_id,
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_versions(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> Sequence[ResumeVersion]:
        statement = (
            select(ResumeVersion)
            .where(
                ResumeVersion.user_id == user_id,
                ResumeVersion.variant == variant,
            )
            .order_by(ResumeVersion.version_number.desc())
        )

        result = await self.session.execute(statement)

        return result.scalars().all()

    async def clear_active_variant(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> None:
        statement = (
            update(ResumeVersion)
            .where(
                ResumeVersion.user_id == user_id,
                ResumeVersion.variant == variant,
                ResumeVersion.is_active.is_(True),
            )
            .values(is_active=False)
        )

        await self.session.execute(statement)

    async def add_submission(
        self,
        submission: ResumeVersionSubmission,
    ) -> ResumeVersionSubmission:
        self.session.add(submission)

        await self.session.flush()
        await self.session.refresh(submission)

        return submission

    async def list_submissions(
        self,
        *,
        resume_version_id: UUID,
    ) -> Sequence[ResumeVersionSubmission]:
        statement = (
            select(ResumeVersionSubmission)
            .where(ResumeVersionSubmission.resume_version_id == resume_version_id)
            .order_by(ResumeVersionSubmission.submitted_at.desc())
        )

        result = await self.session.execute(statement)

        return result.scalars().all()

    async def get_submission_for_application(
        self,
        *,
        user_id: UUID,
        application_reference: str,
    ) -> ResumeVersionSubmission | None:
        statement = (
            select(ResumeVersionSubmission)
            .join(
                ResumeVersion,
                ResumeVersion.id == ResumeVersionSubmission.resume_version_id,
            )
            .where(
                ResumeVersion.user_id == user_id,
                ResumeVersionSubmission.application_reference == application_reference,
            )
            .order_by(ResumeVersionSubmission.submitted_at.desc())
            .limit(1)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
