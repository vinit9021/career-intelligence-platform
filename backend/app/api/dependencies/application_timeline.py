from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import DbSession
from app.repositories.application_timeline import (
    ApplicationTimelineRepository,
)
from app.repositories.applications import (
    ApplicationRepository,
)
from app.services.application_timeline import (
    ApplicationTimelineService,
)


def get_application_timeline_service(
    session: DbSession,
) -> ApplicationTimelineService:
    return ApplicationTimelineService(
        session=session,
        application_repository=(ApplicationRepository(session)),
        timeline_repository=(ApplicationTimelineRepository(session)),
    )


ApplicationTimelineServiceDependency = Annotated[
    ApplicationTimelineService,
    Depends(get_application_timeline_service),
]
