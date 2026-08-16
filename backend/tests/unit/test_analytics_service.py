from datetime import UTC, date, datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models import User
from app.repositories.analytics import (
    AnalyticsRepository,
    RecentActivityRecord,
)
from app.schemas.application import (
    ApplicationStatus,
)
from app.services.analytics import (
    AnalyticsService,
)


class FakeAnalyticsRepository:
    def __init__(self) -> None:
        self.status_counts: dict[
            ApplicationStatus,
            int,
        ] = {}

        self.application_dates: list[date] = []

        self.activity: list[RecentActivityRecord] = []

        self.user_ids: list[UUID] = []

    async def get_status_counts(
        self,
        *,
        user_id: UUID,
    ) -> dict[
        ApplicationStatus,
        int,
    ]:
        self.user_ids.append(user_id)

        return self.status_counts

    async def get_application_dates(
        self,
        *,
        user_id: UUID,
    ) -> list[date]:
        self.user_ids.append(user_id)

        return self.application_dates

    async def get_recent_activity(
        self,
        *,
        user_id: UUID,
        limit: int = 8,
    ) -> list[RecentActivityRecord]:
        self.user_ids.append(user_id)

        return self.activity[:limit]


def make_user() -> User:
    return User(
        id=uuid4(),
        email=("analytics@example.com"),
        password_hash="hash",
        full_name=("Analytics User"),
    )


def make_service(
    repository: (FakeAnalyticsRepository),
) -> AnalyticsService:
    return AnalyticsService(
        session=cast(
            AsyncSession,
            object(),
        ),
        repository=cast(
            AnalyticsRepository,
            repository,
        ),
    )


@pytest.mark.asyncio
async def test_analytics_summary() -> None:
    repository = FakeAnalyticsRepository()

    repository.status_counts = {
        "applied": 4,
        "online_assessment": 2,
        "interview": 2,
        "offer": 1,
        "rejected": 1,
    }

    service = make_service(repository)

    result = await service.get_overview(user=make_user())

    assert result.summary.total_applications == 10

    assert result.summary.active_applications == 8

    assert result.summary.online_assessments == 2

    assert result.summary.interviews == 2

    assert result.summary.offers == 1

    assert result.summary.rejections == 1

    assert result.summary.active_rate == 80.0

    assert result.summary.interview_rate == 20.0

    assert result.summary.offer_rate == 10.0


@pytest.mark.asyncio
async def test_zero_data_analytics() -> None:
    repository = FakeAnalyticsRepository()

    service = make_service(repository)

    result = await service.get_overview(user=make_user())

    assert result.summary.total_applications == 0

    assert result.summary.active_rate == 0.0

    assert result.summary.offer_rate == 0.0

    assert all(item.count == 0 for item in result.status_breakdown)


@pytest.mark.asyncio
async def test_recent_activity() -> None:
    repository = FakeAnalyticsRepository()

    application_id = uuid4()

    repository.activity = [
        RecentActivityRecord(
            event_id=uuid4(),
            application_id=(application_id),
            company="Amazon",
            role=("Applied Scientist Intern"),
            event_type=("status_changed"),
            title=("Status changed to Interview"),
            source="system",
            event_at=datetime.now(UTC),
        )
    ]

    service = make_service(repository)

    result = await service.get_overview(user=make_user())

    assert len(result.recent_activity) == 1

    activity = result.recent_activity[0]

    assert activity.application_id == application_id

    assert activity.company == "Amazon"


@pytest.mark.asyncio
async def test_analytics_uses_authenticated_user() -> None:
    repository = FakeAnalyticsRepository()

    user = make_user()

    service = make_service(repository)

    await service.get_overview(user=user)

    assert repository.user_ids

    assert all(user_id == user.id for user_id in repository.user_ids)


@pytest.mark.asyncio
async def test_status_breakdown_contains_all_statuses() -> None:
    repository = FakeAnalyticsRepository()

    repository.status_counts = {
        "applied": 1,
    }

    service = make_service(repository)

    result = await service.get_overview(user=make_user())

    statuses = {item.status for item in result.status_breakdown}

    assert statuses == {
        "applied",
        "online_assessment",
        "interview",
        "offer",
        "rejected",
        "withdrawn",
    }
