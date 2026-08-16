from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import (
    DbSession,
)
from app.services.analytics import (
    AnalyticsService,
)


def get_analytics_service(
    session: DbSession,
) -> AnalyticsService:
    return AnalyticsService(session=session)


AnalyticsServiceDependency = Annotated[
    AnalyticsService,
    Depends(get_analytics_service),
]
