"""Deterministic Resume Version Manager Agent."""

from __future__ import annotations

from uuid import UUID

from app.schemas.resume_version import (
    ResumeSubmissionCreate,
    ResumeSubmissionRead,
    ResumeVariant,
    ResumeVersionCreate,
    ResumeVersionHistory,
    ResumeVersionRead,
)
from app.services.resume_versions import (
    ResumeVersionManagerService,
)


class ResumeVersionManagerAgent:
    """Specialized deterministic version manager."""

    def __init__(
        self,
        service: ResumeVersionManagerService,
    ) -> None:
        self.service = service

    async def create_variant(
        self,
        request: ResumeVersionCreate,
    ) -> ResumeVersionRead:
        return await self.service.create_version(request)

    async def get_history(
        self,
        *,
        user_id: UUID,
        variant: ResumeVariant,
    ) -> ResumeVersionHistory:
        return await self.service.list_history(
            user_id=user_id,
            variant=variant,
        )

    async def set_active(
        self,
        *,
        user_id: UUID,
        version_id: UUID,
    ) -> ResumeVersionRead:
        return await self.service.activate_version(
            user_id=user_id,
            version_id=version_id,
        )

    async def track_submission(
        self,
        request: ResumeSubmissionCreate,
    ) -> ResumeSubmissionRead:
        return await self.service.record_submission(request)

    async def submitted_version(
        self,
        *,
        user_id: UUID,
        application_reference: str,
    ) -> ResumeVersionRead | None:
        return await self.service.get_submitted_version(
            user_id=user_id,
            application_reference=(application_reference),
        )
