from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Resume


class ResumeLibraryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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

    async def get_with_parse_result_for_user(
        self,
        *,
        resume_id: UUID,
        user_id: UUID,
    ) -> Resume | None:
        resume: Resume | None = await self._session.scalar(
            select(Resume)
            .options(selectinload(Resume.parse_result))
            .where(
                Resume.id == resume_id,
                Resume.user_id == user_id,
            )
        )
        return resume

    async def count_for_user(self, user_id: UUID) -> int:
        count_value: int | None = await self._session.scalar(
            select(func.count()).select_from(Resume).where(Resume.user_id == user_id)
        )
        return count_value or 0

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        offset: int,
        limit: int,
    ) -> list[Resume]:
        result = await self._session.scalars(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc(), Resume.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.all())

    async def delete(self, resume: Resume) -> None:
        await self._session.delete(resume)
