from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

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
from app.schemas.application_timeline import (
    ApplicationTimelineCreateRequest,
    ApplicationTimelineUpdateRequest,
)
from app.services.application_timeline import (
    ApplicationTimelineService,
    TimelineApplicationNotFoundError,
)


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.refreshes = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def refresh(
        self,
        value: object,
    ) -> None:
        del value
        self.refreshes += 1


class FakeApplicationRepository:
    def __init__(
        self,
        application: Application | None,
    ) -> None:
        self.application = application
        self.user_id: UUID | None = None

    async def get_by_id_for_user(
        self,
        *,
        application_id: UUID,
        user_id: UUID,
    ) -> Application | None:
        del application_id
        self.user_id = user_id
        return self.application


class FakeTimelineRepository:
    def __init__(self) -> None:
        self.events: list[ApplicationTimelineEvent] = []

    def add(
        self,
        event: ApplicationTimelineEvent,
    ) -> None:
        self.events.append(event)

    async def list_for_application(
        self,
        *,
        application_id: UUID,
        user_id: UUID,
        order: str,
    ) -> list[ApplicationTimelineEvent]:
        del application_id
        del user_id
        del order
        return self.events

    async def get_for_application(
        self,
        *,
        event_id: UUID,
        application_id: UUID,
        user_id: UUID,
    ) -> ApplicationTimelineEvent | None:
        del application_id
        del user_id

        for event in self.events:
            if event.id == event_id:
                return event

        return None

    async def delete(
        self,
        event: ApplicationTimelineEvent,
    ) -> None:
        self.events.remove(event)


def make_user() -> User:
    return User(
        id=uuid4(),
        email="timeline@example.com",
        password_hash="hash",
        full_name="Timeline User",
    )


def make_application(
    user: User,
) -> Application:
    return Application(
        id=uuid4(),
        user_id=user.id,
        company="Amazon",
        role="Applied Scientist Intern",
        applied_at=datetime.now(UTC).date(),
        status="applied",
        source="manual",
    )


def make_service(
    *,
    application: Application | None,
) -> tuple[
    ApplicationTimelineService,
    FakeSession,
    FakeTimelineRepository,
]:
    session = FakeSession()

    application_repository = FakeApplicationRepository(application)

    timeline_repository = FakeTimelineRepository()

    service = ApplicationTimelineService(
        session=cast(
            AsyncSession,
            session,
        ),
        application_repository=cast(
            ApplicationRepository,
            application_repository,
        ),
        timeline_repository=cast(
            ApplicationTimelineRepository,
            timeline_repository,
        ),
    )

    return (
        service,
        session,
        timeline_repository,
    )


@pytest.mark.asyncio
async def test_create_timeline_event() -> None:
    user = make_user()

    application = make_application(user)

    service, session, repository = make_service(application=application)

    result = await service.create(
        application_id=application.id,
        user=user,
        payload=(
            ApplicationTimelineCreateRequest(
                event_type="note",
                title="Recruiter follow-up",
                description=("Followed up with recruiter."),
            )
        ),
    )

    assert result.application_id == application.id

    assert result.user_id == user.id
    assert result.source == "manual"
    assert len(repository.events) == 1
    assert session.commits == 1


@pytest.mark.asyncio
async def test_list_timeline_events() -> None:
    user = make_user()

    application = make_application(user)

    service, _, repository = make_service(application=application)

    repository.events.append(
        ApplicationTimelineEvent(
            id=uuid4(),
            application_id=application.id,
            user_id=user.id,
            event_type="note",
            title="Test event",
            source="manual",
            event_at=datetime.now(UTC),
        )
    )

    events = await service.list_events(
        application_id=application.id,
        user=user,
        order="asc",
    )

    assert len(events) == 1


@pytest.mark.asyncio
async def test_update_timeline_event() -> None:
    user = make_user()

    application = make_application(user)

    service, session, repository = make_service(application=application)

    event = ApplicationTimelineEvent(
        id=uuid4(),
        application_id=application.id,
        user_id=user.id,
        event_type="note",
        title="Old title",
        source="manual",
        event_at=datetime.now(UTC),
    )

    repository.events.append(event)

    result = await service.update(
        event_id=event.id,
        application_id=application.id,
        user=user,
        payload=(ApplicationTimelineUpdateRequest(title="Updated title")),
    )

    assert result.title == "Updated title"

    assert session.commits == 1


@pytest.mark.asyncio
async def test_delete_timeline_event() -> None:
    user = make_user()

    application = make_application(user)

    service, session, repository = make_service(application=application)

    event = ApplicationTimelineEvent(
        id=uuid4(),
        application_id=application.id,
        user_id=user.id,
        event_type="note",
        title="Delete me",
        source="manual",
        event_at=datetime.now(UTC),
    )

    repository.events.append(event)

    await service.delete(
        event_id=event.id,
        application_id=application.id,
        user=user,
    )

    assert repository.events == []
    assert session.commits == 1


@pytest.mark.asyncio
async def test_user_cannot_access_foreign_application() -> None:
    user = make_user()

    service, _, _ = make_service(application=None)

    with pytest.raises(TimelineApplicationNotFoundError):
        await service.list_events(
            application_id=uuid4(),
            user=user,
            order="asc",
        )
