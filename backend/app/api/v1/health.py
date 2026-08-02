from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])

SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check API health",
    description="Returns the current API status and application metadata.",
)
def read_health(settings: SettingsDependency) -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        environment=settings.app_env,
        version=settings.app_version,
    )
