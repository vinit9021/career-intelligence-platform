from __future__ import annotations

from datetime import date
from typing import cast
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Application,
    ApplicationTimelineEvent,
    User,
)
from app.repositories.application_timeline import (
    ApplicationTimelineRepository,
)
from app.repositories.applications import (
    ApplicationRepository,
)
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
)
from app.services.applications import (
    ApplicationService,
)


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        pass

    async def refresh(
        self,
        value: object,
    ) -> None:
        del value


class FakeApplicationRepository:
    def __init__(
        self,
        application: Application | None = None,
    ) -> None:
        self.application = application

    def add(
        self,
        application: Application,
    ) -> None:
        self.application = application

    async def get_by_id_for_user(
        self,
        *,
        application_id: object,
        user_id: object,
    ) -> Application | None:
        del application_id
        del user_id
        return self.application


class FakeTimelineRepository:
    def __init__(self) -> None:
        self.events: list[ApplicationTimelineEvent] = []

    def add(
        self,
        event: ApplicationTimelineEvent,
    ) -> None:
        self.events.append(event)


def make_user() -> User:
    return User(
        id=uuid4(),
        email="auto@example.com",
        password_hash="hash",
        full_name="Auto User",
    )


@pytest.mark.asyncio
async def test_create_application_adds_initial_event() -> None:
    user = make_user()

    session = FakeSession()

    application_repository = FakeApplicationRepository()

    timeline_repository = FakeTimelineRepository()

    service = ApplicationService(
        session=cast(
            AsyncSession,
            session,
        ),
        repository=cast(
            ApplicationRepository,
            application_repository,
        ),
        timeline_repository=cast(
            ApplicationTimelineRepository,
            timeline_repository,
        ),
    )

    application = await service.create(
        user=user,
        payload=(
            ApplicationCreateRequest(
                company="Amazon",
                role="Applied Scientist Intern",
                applied_at=date(
                    2026,
                    8,
                    15,
                ),
            )
        ),
    )

    assert application.id is not None
    assert len(timeline_repository.events) == 1

    event = timeline_repository.events[0]

    assert event.event_type == "application_submitted"

    assert event.source == "system"


@pytest.mark.asyncio
async def test_status_change_adds_timeline_event() -> None:
    user = make_user()

    application = Application(
        id=uuid4(),
        user_id=user.id,
        company="Amazon",
        role="Applied Scientist Intern",
        applied_at=date(
            2026,
            8,
            15,
        ),
        status="applied",
        source="manual",
    )

    session = FakeSession()

    application_repository = FakeApplicationRepository(application)

    timeline_repository = FakeTimelineRepository()

    service = ApplicationService(
        session=cast(
            AsyncSession,
            session,
        ),
        repository=cast(
            ApplicationRepository,
            application_repository,
        ),
        timeline_repository=cast(
            ApplicationTimelineRepository,
            timeline_repository,
        ),
    )

    updated = await service.update(
        user=user,
        application_id=application.id,
        payload=(ApplicationUpdateRequest(status="interview")),
    )

    assert updated.status == "interview"

    assert len(timeline_repository.events) == 1

    event = timeline_repository.events[0]

    assert event.event_type == "status_changed"

    assert event.related_status == "interview"

    assert event.source == "system"
