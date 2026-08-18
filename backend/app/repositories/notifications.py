from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    func,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    def add(
        self,
        notification: Notification,
    ) -> None:
        self._session.add(notification)

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
        conditions = [Notification.user_id == user_id]

        if unread_only:
            conditions.append(Notification.is_read.is_(False))

        total_value = await self._session.scalar(
            select(func.count()).select_from(Notification).where(*conditions)
        )

        result = await self._session.scalars(
            select(Notification)
            .where(*conditions)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return (
            list(result.all()),
            int(total_value or 0),
        )

    async def get_for_user(
        self,
        *,
        notification_id: UUID,
        user_id: UUID,
    ) -> Notification | None:
        notification: Notification | None = await self._session.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )

        return notification

    async def unread_count(
        self,
        *,
        user_id: UUID,
    ) -> int:
        value = await self._session.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )

        return int(value or 0)

    async def mark_all_read(
        self,
        *,
        user_id: UUID,
        read_at: datetime,
    ) -> None:
        await self._session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(
                is_read=True,
                read_at=read_at,
            )
        )

    async def delete(
        self,
        notification: Notification,
    ) -> None:
        await self._session.delete(notification)
