from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import DbSession
from app.services.notifications import (
    NotificationService,
)


def get_notification_service(
    session: DbSession,
) -> NotificationService:
    return NotificationService(session=session)


NotificationServiceDependency = Annotated[
    NotificationService,
    Depends(get_notification_service),
]
