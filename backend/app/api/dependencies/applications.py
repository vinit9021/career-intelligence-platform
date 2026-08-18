from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import DbSession
from app.repositories.application_timeline import (
    ApplicationTimelineRepository,
)
from app.repositories.notifications import (
    NotificationRepository,
)
from app.services.applications import (
    ApplicationService,
)


def get_application_service(
    session: DbSession,
) -> ApplicationService:
    return ApplicationService(
        session=session,
        timeline_repository=(ApplicationTimelineRepository(session)),
        notification_repository=(NotificationRepository(session)),
    )


ApplicationServiceDependency = Annotated[
    ApplicationService,
    Depends(get_application_service),
]
