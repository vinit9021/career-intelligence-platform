from dataclasses import dataclass
from datetime import date, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models import Application
from app.models.application_timeline import (
    ApplicationTimelineEvent,
)
from app.schemas.application import (
    ApplicationStatus,
)
from app.schemas.application_timeline import (
    TimelineEventSource,
    TimelineEventType,
)


@dataclass(frozen=True)
class RecentActivityRecord:
    event_id: UUID
    application_id: UUID

    company: str
    role: str

    event_type: TimelineEventType
    title: str
    source: TimelineEventSource

    event_at: datetime


class AnalyticsRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_status_counts(
        self,
        *,
        user_id: UUID,
    ) -> dict[
        ApplicationStatus,
        int,
    ]:
        statement = (
            select(
                Application.status,
                func.count(Application.id),
            )
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )

        result = await self._session.execute(statement)

        counts: dict[
            ApplicationStatus,
            int,
        ] = {}

        for status_value, count in result.all():
            status_name = cast(
                ApplicationStatus,
                status_value,
            )

            counts[status_name] = int(count)

        return counts

    async def get_application_dates(
        self,
        *,
        user_id: UUID,
    ) -> list[date]:
        result = await self._session.scalars(
            select(Application.applied_at).where(Application.user_id == user_id)
        )

        return list(result.all())

    async def get_recent_activity(
        self,
        *,
        user_id: UUID,
        limit: int = 8,
    ) -> list[RecentActivityRecord]:
        statement = (
            select(
                ApplicationTimelineEvent,
                Application.company,
                Application.role,
            )
            .join(
                Application,
                Application.id == ApplicationTimelineEvent.application_id,
            )
            .where(
                ApplicationTimelineEvent.user_id == user_id,
                Application.user_id == user_id,
            )
            .order_by(
                ApplicationTimelineEvent.event_at.desc(),
                ApplicationTimelineEvent.created_at.desc(),
            )
            .limit(limit)
        )

        result = await self._session.execute(statement)

        records: list[RecentActivityRecord] = []

        for (
            event_value,
            company_value,
            role_value,
        ) in result.all():
            event = cast(
                ApplicationTimelineEvent,
                event_value,
            )

            records.append(
                RecentActivityRecord(
                    event_id=event.id,
                    application_id=(event.application_id),
                    company=str(company_value),
                    role=str(role_value),
                    event_type=cast(
                        TimelineEventType,
                        event.event_type,
                    ),
                    title=event.title,
                    source=cast(
                        TimelineEventSource,
                        event.source,
                    ),
                    event_at=event.event_at,
                )
            )

        return records
