from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Resume, ResumeParseResult


class ResumeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, resume: Resume) -> None:
        self._session.add(resume)

    async def get_by_id_for_user(
        self,
        *,
        resume_id: UUID,
        user_id: UUID,
    ) -> Resume | None:
        resume: Resume | None = await self._session.scalar(
            select(Resume).where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
            )
        )
        return resume


class ResumeParseResultRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, result: ResumeParseResult) -> None:
        self._session.add(result)

    async def get_by_resume_id(self, resume_id: UUID) -> ResumeParseResult | None:
        result: ResumeParseResult | None = await self._session.scalar(
            select(ResumeParseResult).where(ResumeParseResult.resume_id == resume_id)
        )
        return result
