from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    status,
)

from app.api.dependencies import (
    CurrentUser,
)
from app.api.dependencies.applications import (
    ApplicationServiceDependency,
)
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationPageResponse,
    ApplicationResponse,
    ApplicationSortField,
    ApplicationStatus,
    ApplicationUpdateRequest,
    SortOrder,
)
from app.services.applications import (
    ApplicationNotFoundError,
    ApplicationPersistenceError,
)

router = APIRouter(
    prefix="/applications",
    tags=["applications"],
)


@router.post(
    "",
    response_model=(ApplicationResponse),
    status_code=(status.HTTP_201_CREATED),
)
async def create_application(
    payload: ApplicationCreateRequest,
    current_user: CurrentUser,
    service: (ApplicationServiceDependency),
) -> ApplicationResponse:
    try:
        application = await service.create(
            user=current_user,
            payload=payload,
            source="manual",
        )
    except ApplicationPersistenceError as exc:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    return ApplicationResponse.model_validate(application)


@router.get(
    "",
    response_model=(ApplicationPageResponse),
)
async def list_applications(
    current_user: CurrentUser,
    service: (ApplicationServiceDependency),
    search: Annotated[
        str | None,
        Query(max_length=200),
    ] = None,
    status_filter: Annotated[
        ApplicationStatus | None,
        Query(alias="status"),
    ] = None,
    sort_by: Annotated[
        ApplicationSortField,
        Query(),
    ] = "applied_at",
    sort_order: Annotated[
        SortOrder,
        Query(),
    ] = "desc",
    page: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 20,
) -> ApplicationPageResponse:
    applications, total = await service.list_for_user(
        user=current_user,
        search=search,
        status=status_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return ApplicationPageResponse(
        items=[ApplicationResponse.model_validate(application) for application in applications],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
async def get_application(
    application_id: UUID,
    current_user: CurrentUser,
    service: ApplicationServiceDependency,
) -> ApplicationResponse:
    try:
        application = await service.get(
            user=current_user,
            application_id=application_id,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ApplicationResponse.model_validate(
        application
    )


@router.patch(
    "/{application_id}",
    response_model=(ApplicationResponse),
)
async def update_application(
    application_id: UUID,
    payload: (ApplicationUpdateRequest),
    current_user: CurrentUser,
    service: (ApplicationServiceDependency),
) -> ApplicationResponse:
    try:
        application = await service.update(
            user=current_user,
            application_id=(application_id),
            payload=payload,
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail=str(exc),
        ) from exc
    except ApplicationPersistenceError as exc:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    return ApplicationResponse.model_validate(application)


@router.delete(
    "/{application_id}",
    status_code=(status.HTTP_204_NO_CONTENT),
)
async def delete_application(
    application_id: UUID,
    current_user: CurrentUser,
    service: (ApplicationServiceDependency),
) -> Response:
    try:
        await service.delete(
            user=current_user,
            application_id=(application_id),
        )
    except ApplicationNotFoundError as exc:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail=str(exc),
        ) from exc
    except ApplicationPersistenceError as exc:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    return Response(status_code=(status.HTTP_204_NO_CONTENT))
