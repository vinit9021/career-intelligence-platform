from __future__ import annotations

from datetime import date
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Application,
    User,
)
from app.repositories.applications import (
    ApplicationRepository,
)
from app.services.applications import (
    ApplicationNotFoundError,
    ApplicationService,
)


class FakeSession:
    pass


class CapturingRepository:
    def __init__(
        self,
        application: Application | None,
    ) -> None:
        self.application = application

        self.application_id: UUID | None = None
        self.user_id: UUID | None = None

    async def get_by_id_for_user(
        self,
        *,
        application_id: UUID,
        user_id: UUID,
    ) -> Application | None:
        self.application_id = application_id
        self.user_id = user_id

        return self.application


def make_user() -> User:
    return User(
        id=uuid4(),
        email="details@example.com",
        password_hash="hash",
        full_name="Details User",
    )


def make_application(
    user: User,
) -> Application:
    return Application(
        id=uuid4(),
        user_id=user.id,
        company="Microsoft",
        role="Software Engineer",
        location="Bengaluru",
        applied_at=date(
            2026,
            8,
            13,
        ),
        status="applied",
        source="manual",
        notes="Applied through careers portal.",
    )


@pytest.mark.asyncio
async def test_get_application() -> None:
    user = make_user()

    application = make_application(
        user
    )

    repository = CapturingRepository(
        application
    )

    service = ApplicationService(
        session=cast(
            AsyncSession,
            FakeSession(),
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    result = await service.get(
        user=user,
        application_id=application.id,
    )

    assert result is application

    assert (
        repository.application_id
        == application.id
    )

    assert (
        repository.user_id
        == user.id
    )


@pytest.mark.asyncio
async def test_get_application_enforces_user_scope() -> None:
    owner = make_user()

    another_user = User(
        id=uuid4(),
        email="other@example.com",
        password_hash="hash",
        full_name="Other User",
    )

    application = make_application(
        owner
    )

    repository = CapturingRepository(
        None
    )

    service = ApplicationService(
        session=cast(
            AsyncSession,
            FakeSession(),
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    with pytest.raises(
        ApplicationNotFoundError
    ):
        await service.get(
            user=another_user,
            application_id=application.id,
        )

    assert (
        repository.user_id
        == another_user.id
    )


@pytest.mark.asyncio
async def test_get_missing_application() -> None:
    user = make_user()

    repository = CapturingRepository(
        None
    )

    service = ApplicationService(
        session=cast(
            AsyncSession,
            FakeSession(),
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    with pytest.raises(
        ApplicationNotFoundError,
        match="Application not found",
    ):
        await service.get(
            user=user,
            application_id=uuid4(),
        )
