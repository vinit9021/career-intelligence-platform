from __future__ import annotations

from datetime import date
from typing import cast
from uuid import uuid4

import pytest

from app.models import (
    Application,
    User,
)
from app.repositories.applications import (
    ApplicationRepository,
)
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
)
from app.services.applications import (
    ApplicationNotFoundError,
    ApplicationService,
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


class FakeRepository:
    def __init__(self) -> None:
        self.added: Application | None = None

        self.application: Application | None = None

        self.deleted: Application | None = None

    def add(
        self,
        application: Application,
    ) -> None:
        self.added = application

    async def get_by_id_for_user(
        self,
        *,
        application_id: object,
        user_id: object,
    ) -> Application | None:
        del application_id
        del user_id

        return self.application

    async def list_for_user(
        self,
        **kwargs: object,
    ) -> tuple[
        list[Application],
        int,
    ]:
        del kwargs

        if self.application is None:
            return [], 0

        return [self.application], 1

    async def delete(
        self,
        application: Application,
    ) -> None:
        self.deleted = application


def make_user() -> User:
    return User(
        id=uuid4(),
        email="user@example.com",
        password_hash="hash",
        full_name="Test User",
    )


def make_application(
    user: User,
) -> Application:
    return Application(
        id=uuid4(),
        user_id=user.id,
        company="Google",
        role="Software Engineer",
        applied_at=date(
            2026,
            8,
            13,
        ),
        status="applied",
        source="manual",
    )


@pytest.mark.asyncio
async def test_create_application() -> None:
    session = FakeSession()

    repository = FakeRepository()

    user = make_user()

    service = ApplicationService(
        session=cast(
            object,
            session,
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    result = await service.create(
        user=user,
        payload=(
            ApplicationCreateRequest(
                company="Google",
                role=("Software Engineer"),
                applied_at=date(
                    2026,
                    8,
                    13,
                ),
            )
        ),
    )

    assert result.company == "Google"

    assert result.user_id == user.id

    assert result.source == "manual"

    assert session.commits == 1

    assert repository.added is result


@pytest.mark.asyncio
async def test_list_applications() -> None:
    session = FakeSession()

    repository = FakeRepository()

    user = make_user()

    repository.application = make_application(user)

    service = ApplicationService(
        session=cast(
            object,
            session,
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    items, total = await service.list_for_user(
        user=user,
        search=None,
        status=None,
        sort_by="applied_at",
        sort_order="desc",
        page=1,
        page_size=20,
    )

    assert total == 1

    assert len(items) == 1


@pytest.mark.asyncio
async def test_update_application() -> None:
    session = FakeSession()

    repository = FakeRepository()

    user = make_user()

    repository.application = make_application(user)

    service = ApplicationService(
        session=cast(
            object,
            session,
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    result = await service.update(
        user=user,
        application_id=(repository.application.id),
        payload=(ApplicationUpdateRequest(status="interview")),
    )

    assert result.status == "interview"

    assert session.commits == 1


@pytest.mark.asyncio
async def test_update_missing_application() -> None:
    session = FakeSession()

    repository = FakeRepository()

    service = ApplicationService(
        session=cast(
            object,
            session,
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    with pytest.raises(ApplicationNotFoundError):
        await service.update(
            user=make_user(),
            application_id=uuid4(),
            payload=(ApplicationUpdateRequest(status="offer")),
        )


@pytest.mark.asyncio
async def test_delete_application() -> None:
    session = FakeSession()

    repository = FakeRepository()

    user = make_user()

    repository.application = make_application(user)

    service = ApplicationService(
        session=cast(
            object,
            session,
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    await service.delete(
        user=user,
        application_id=(repository.application.id),
    )

    assert repository.deleted is repository.application

    assert session.commits == 1


@pytest.mark.asyncio
async def test_delete_missing_application() -> None:
    session = FakeSession()

    repository = FakeRepository()

    service = ApplicationService(
        session=cast(
            object,
            session,
        ),
        repository=cast(
            ApplicationRepository,
            repository,
        ),
    )

    with pytest.raises(ApplicationNotFoundError):
        await service.delete(
            user=make_user(),
            application_id=uuid4(),
        )
