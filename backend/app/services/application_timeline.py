from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.application_timeline import (
    ApplicationTimelineEvent,
)
from app.repositories.application_timeline import (
    ApplicationTimelineRepository,
)
from app.repositories.applications import (
    ApplicationRepository,
)
from app.schemas.application_timeline import (
    ApplicationTimelineCreateRequest,
    ApplicationTimelineUpdateRequest,
    TimelineSortOrder,
)


class TimelineApplicationNotFoundError(LookupError):
    pass


class TimelineEventNotFoundError(LookupError):
    pass


class TimelinePersistenceError(RuntimeError):
    pass


class ApplicationTimelineService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        application_repository: (ApplicationRepository | None) = None,
        timeline_repository: (ApplicationTimelineRepository | None) = None,
    ) -> None:
        self._session = session

        self._application_repository = (
            application_repository
            if application_repository is not None
            else ApplicationRepository(session)
        )

        self._timeline_repository = (
            timeline_repository
            if timeline_repository is not None
            else ApplicationTimelineRepository(session)
        )

    async def _ensure_application(
        self,
        *,
        application_id: UUID,
        user: User,
    ) -> None:
        application = await self._application_repository.get_by_id_for_user(
            application_id=application_id,
            user_id=user.id,
        )

        if application is None:
            raise TimelineApplicationNotFoundError("Application not found.")

    async def list_events(
        self,
        *,
        application_id: UUID,
        user: User,
        order: TimelineSortOrder,
    ) -> list[ApplicationTimelineEvent]:
        await self._ensure_application(
            application_id=application_id,
            user=user,
        )

        return await self._timeline_repository.list_for_application(
            application_id=application_id,
            user_id=user.id,
            order=order,
        )

    async def create(
        self,
        *,
        application_id: UUID,
        user: User,
        payload: ApplicationTimelineCreateRequest,
        source: str = "manual",
        external_id: str | None = None,
    ) -> ApplicationTimelineEvent:
        await self._ensure_application(
            application_id=application_id,
            user=user,
        )

        event = ApplicationTimelineEvent(
            application_id=application_id,
            user_id=user.id,
            source=source,
            external_id=external_id,
            **payload.model_dump(),
        )

        self._timeline_repository.add(event)

        try:
            await self._session.commit()

            await self._session.refresh(event)
        except Exception as exc:
            await self._session.rollback()

            raise TimelinePersistenceError("The timeline event could not be saved.") from exc

        return event

    async def update(
        self,
        *,
        event_id: UUID,
        application_id: UUID,
        user: User,
        payload: ApplicationTimelineUpdateRequest,
    ) -> ApplicationTimelineEvent:
        await self._ensure_application(
            application_id=application_id,
            user=user,
        )

        event = await self._timeline_repository.get_for_application(
            event_id=event_id,
            application_id=application_id,
            user_id=user.id,
        )

        if event is None:
            raise TimelineEventNotFoundError("Timeline event not found.")

        data: dict[str, Any] = payload.model_dump(exclude_unset=True)

        for field_name, value in data.items():
            setattr(
                event,
                field_name,
                value,
            )

        try:
            await self._session.commit()

            await self._session.refresh(event)
        except Exception as exc:
            await self._session.rollback()

            raise TimelinePersistenceError("The timeline event could not be updated.") from exc

        return event

    async def delete(
        self,
        *,
        event_id: UUID,
        application_id: UUID,
        user: User,
    ) -> None:
        await self._ensure_application(
            application_id=application_id,
            user=user,
        )

        event = await self._timeline_repository.get_for_application(
            event_id=event_id,
            application_id=application_id,
            user_id=user.id,
        )

        if event is None:
            raise TimelineEventNotFoundError("Timeline event not found.")

        await self._timeline_repository.delete(event)

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()

            raise TimelinePersistenceError("The timeline event could not be deleted.") from exc
