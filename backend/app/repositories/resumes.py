from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models import Resume


class ResumeRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    def add(
        self,
        resume: Resume,
    ) -> None:
        self._session.add(resume)
