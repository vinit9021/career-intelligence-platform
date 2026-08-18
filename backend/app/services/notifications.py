from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.models.notification import Notification
from app.repositories.notifications import (
    NotificationRepository,
)
from app.schemas.notification import (
    NotificationSource,
    NotificationType,
)


class NotificationNotFoundError(LookupError):
    pass


class NotificationPersistenceError(RuntimeError):
    pass


class NotificationService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        repository: (NotificationRepository | None) = None,
    ) -> None:
        self._session = session

        self._repository = repository if repository is not None else NotificationRepository(session)

    async def create(
        self,
        *,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        application_id: UUID | None = None,
        source: NotificationSource = "system",
        commit: bool = True,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            application_id=application_id,
            type=notification_type,
            title=title,
            message=message,
            source=source,
        )

        self._repository.add(notification)

        if commit:
            try:
                await self._session.commit()

                await self._session.refresh(notification)
            except Exception as exc:
                await self._session.rollback()

                raise (
                    NotificationPersistenceError("The notification could not be saved.")
                ) from exc

        return notification

    async def list_for_user(
        self,
        *,
        user: User,
        unread_only: bool,
        page: int,
        page_size: int,
    ) -> tuple[
        list[Notification],
        int,
    ]:
        return await self._repository.list_for_user(
            user_id=user.id,
            unread_only=unread_only,
            page=page,
            page_size=page_size,
        )

    async def unread_count(
        self,
        *,
        user: User,
    ) -> int:
        return await self._repository.unread_count(user_id=user.id)

    async def mark_read(
        self,
        *,
        user: User,
        notification_id: UUID,
    ) -> Notification:
        notification = await self._repository.get_for_user(
            notification_id=notification_id,
            user_id=user.id,
        )

        if notification is None:
            raise NotificationNotFoundError("Notification not found.")

        notification.is_read = True
        notification.read_at = datetime.now(UTC)

        await self._save(notification)

        return notification

    async def mark_unread(
        self,
        *,
        user: User,
        notification_id: UUID,
    ) -> Notification:
        notification = await self._repository.get_for_user(
            notification_id=notification_id,
            user_id=user.id,
        )

        if notification is None:
            raise NotificationNotFoundError("Notification not found.")

        notification.is_read = False
        notification.read_at = None

        await self._save(notification)

        return notification

    async def mark_all_read(
        self,
        *,
        user: User,
    ) -> None:
        try:
            await self._repository.mark_all_read(
                user_id=user.id,
                read_at=datetime.now(UTC),
            )

            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()

            raise NotificationPersistenceError("Notifications could not be updated.") from exc

    async def delete(
        self,
        *,
        user: User,
        notification_id: UUID,
    ) -> None:
        notification = await self._repository.get_for_user(
            notification_id=notification_id,
            user_id=user.id,
        )

        if notification is None:
            raise NotificationNotFoundError("Notification not found.")

        await self._repository.delete(notification)

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()

            raise NotificationPersistenceError("Notification could not be deleted.") from exc

    async def _save(
        self,
        notification: Notification,
    ) -> None:
        try:
            await self._session.commit()

            await self._session.refresh(notification)
        except Exception as exc:
            await self._session.rollback()

            raise NotificationPersistenceError("Notification could not be updated.") from exc
