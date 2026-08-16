from fastapi import APIRouter

from app.api.dependencies import (
    CurrentUser,
)
from app.api.dependencies.analytics import (
    AnalyticsServiceDependency,
)
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get(
    "/overview",
    response_model=(AnalyticsOverviewResponse),
)
async def get_analytics_overview(
    current_user: CurrentUser,
    service: (AnalyticsServiceDependency),
) -> AnalyticsOverviewResponse:
    return await service.get_overview(user=current_user)
