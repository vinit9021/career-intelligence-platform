from typing import Annotated

from fastapi import Depends

from app.api.dependencies.auth import (
    DbSession,
)
from app.services.applications import (
    ApplicationService,
)


def get_application_service(
    session: DbSession,
) -> ApplicationService:
    return ApplicationService(session=session)


ApplicationServiceDependency = Annotated[
    ApplicationService,
    Depends(get_application_service),
]
