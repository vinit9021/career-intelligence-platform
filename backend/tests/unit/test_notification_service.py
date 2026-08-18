from datetime import datetime
from typing import cast
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, User
from app.repositories.notifications import (
    NotificationRepository,
)
from app.services.notifications import (
    NotificationNotFoundError,
    NotificationService,
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
        self.items: list[Notification] = []

    def add(
        self,
        notification: Notification,
    ) -> None:
        self.items.append(notification)

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        unread_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[
        list[Notification],
        int,
    ]:
        del page
        del page_size

        items = [
            item
            for item in self.items
            if item.user_id == user_id and (not unread_only or not item.is_read)
        ]

        return items, len(items)

    async def get_for_user(
        self,
        *,
        notification_id: UUID,
        user_id: UUID,
    ) -> Notification | None:
        for item in self.items:
            if item.id == notification_id and item.user_id == user_id:
                return item

        return None

    async def unread_count(
        self,
        *,
        user_id: UUID,
    ) -> int:
        return len([item for item in self.items if item.user_id == user_id and not item.is_read])

    async def mark_all_read(
        self,
        *,
        user_id: UUID,
        read_at: datetime,
    ) -> None:
        for item in self.items:
            if item.user_id == user_id and not item.is_read:
                item.is_read = True
                item.read_at = read_at

    async def delete(
        self,
        notification: Notification,
    ) -> None:
        self.items.remove(notification)


def make_user() -> User:
    return User(
        id=uuid4(),
        email="notify@example.com",
        password_hash="hash",
        full_name="Notify User",
    )


def make_service() -> tuple[
    NotificationService,
    FakeSession,
    FakeRepository,
]:
    session = FakeSession()
    repository = FakeRepository()

    service = NotificationService(
        session=cast(
            AsyncSession,
            session,
        ),
        repository=cast(
            NotificationRepository,
            repository,
        ),
    )

    return (
        service,
        session,
        repository,
    )


@pytest.mark.asyncio
async def test_create_notification() -> None:
    service, session, repository = make_service()

    user = make_user()

    result = await service.create(
        user_id=user.id,
        notification_type="general",
        title="Welcome",
        message="Notification created.",
    )

    assert result.user_id == user.id
    assert len(repository.items) == 1
    assert session.commits == 1


@pytest.mark.asyncio
async def test_list_notifications() -> None:
    service, _, repository = make_service()

    user = make_user()

    repository.items.append(
        Notification(
            id=uuid4(),
            user_id=user.id,
            type="general",
            title="Test",
            message="Test",
            source="system",
            is_read=False,
        )
    )

    items, total = await service.list_for_user(
        user=user,
        unread_only=False,
        page=1,
        page_size=20,
    )

    assert total == 1
    assert len(items) == 1


@pytest.mark.asyncio
async def test_unread_count() -> None:
    service, _, repository = make_service()

    user = make_user()

    repository.items.append(
        Notification(
            id=uuid4(),
            user_id=user.id,
            type="general",
            title="Unread",
            message="Unread",
            source="system",
            is_read=False,
        )
    )

    assert await service.unread_count(user=user) == 1


@pytest.mark.asyncio
async def test_mark_read_and_unread() -> None:
    service, _, repository = make_service()

    user = make_user()

    notification = Notification(
        id=uuid4(),
        user_id=user.id,
        type="general",
        title="Status",
        message="Status",
        source="system",
        is_read=False,
    )

    repository.items.append(notification)

    result = await service.mark_read(
        user=user,
        notification_id=notification.id,
    )

    assert result.is_read is True
    assert result.read_at is not None

    result = await service.mark_unread(
        user=user,
        notification_id=notification.id,
    )

    assert result.is_read is False
    assert result.read_at is None


@pytest.mark.asyncio
async def test_mark_all_read() -> None:
    service, _, repository = make_service()

    user = make_user()

    for index in range(2):
        repository.items.append(
            Notification(
                id=uuid4(),
                user_id=user.id,
                type="general",
                title=f"Test {index}",
                message="Test",
                source="system",
                is_read=False,
            )
        )

    await service.mark_all_read(user=user)

    assert all(item.is_read for item in repository.items)


@pytest.mark.asyncio
async def test_delete_notification() -> None:
    service, _, repository = make_service()

    user = make_user()

    notification = Notification(
        id=uuid4(),
        user_id=user.id,
        type="general",
        title="Delete",
        message="Delete",
        source="system",
        is_read=False,
    )

    repository.items.append(notification)

    await service.delete(
        user=user,
        notification_id=notification.id,
    )

    assert repository.items == []


@pytest.mark.asyncio
async def test_notification_user_isolation() -> None:
    service, _, repository = make_service()

    owner = make_user()

    other = User(
        id=uuid4(),
        email="other@example.com",
        password_hash="hash",
        full_name="Other",
    )

    notification = Notification(
        id=uuid4(),
        user_id=owner.id,
        type="general",
        title="Private",
        message="Private",
        source="system",
        is_read=False,
    )

    repository.items.append(notification)

    with pytest.raises(NotificationNotFoundError):
        await service.mark_read(
            user=other,
            notification_id=notification.id,
        )
