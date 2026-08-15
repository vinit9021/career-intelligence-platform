from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_timeline import (
    ApplicationTimelineEvent,
)


class ApplicationTimelineRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    def add(
        self,
        event: ApplicationTimelineEvent,
    ) -> None:
        self._session.add(event)

    async def list_for_application(
        self,
        *,
        application_id: UUID,
        user_id: UUID,
        order: str,
    ) -> list[ApplicationTimelineEvent]:
        sort_expression = (
            ApplicationTimelineEvent.event_at.asc()
            if order == "asc"
            else ApplicationTimelineEvent.event_at.desc()
        )

        result = await self._session.scalars(
            select(ApplicationTimelineEvent)
            .where(
                ApplicationTimelineEvent.application_id == application_id,
                ApplicationTimelineEvent.user_id == user_id,
            )
            .order_by(
                sort_expression,
                ApplicationTimelineEvent.created_at.asc(),
            )
        )

        return list(result.all())

    async def get_for_application(
        self,
        *,
        event_id: UUID,
        application_id: UUID,
        user_id: UUID,
    ) -> ApplicationTimelineEvent | None:
        event: ApplicationTimelineEvent | None = await self._session.scalar(
            select(ApplicationTimelineEvent).where(
                ApplicationTimelineEvent.id == event_id,
                ApplicationTimelineEvent.application_id == application_id,
                ApplicationTimelineEvent.user_id == user_id,
            )
        )

        return event

    async def delete(
        self,
        event: ApplicationTimelineEvent,
    ) -> None:
        await self._session.delete(event)
