from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    status,
)

from app.api.dependencies import CurrentUser
from app.api.dependencies.notifications import (
    NotificationServiceDependency,
)
from app.schemas.notification import (
    NotificationPageResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from app.services.notifications import (
    NotificationNotFoundError,
    NotificationPersistenceError,
)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.get(
    "",
    response_model=NotificationPageResponse,
)
async def list_notifications(
    current_user: CurrentUser,
    service: NotificationServiceDependency,
    unread_only: Annotated[
        bool,
        Query(),
    ] = False,
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
) -> NotificationPageResponse:
    notifications, total = await service.list_for_user(
        user=current_user,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )

    return NotificationPageResponse(
        items=[NotificationResponse.model_validate(notification) for notification in notifications],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/unread-count",
    response_model=(NotificationUnreadCountResponse),
)
async def get_unread_count(
    current_user: CurrentUser,
    service: NotificationServiceDependency,
) -> NotificationUnreadCountResponse:
    count = await service.unread_count(user=current_user)

    return NotificationUnreadCountResponse(unread_count=count)


@router.patch(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_all_notifications_read(
    current_user: CurrentUser,
    service: NotificationServiceDependency,
) -> Response:
    try:
        await service.mark_all_read(user=current_user)
    except NotificationPersistenceError as exc:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
    service: NotificationServiceDependency,
) -> NotificationResponse:
    try:
        notification = await service.mark_read(
            user=current_user,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except NotificationPersistenceError as exc:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    return NotificationResponse.model_validate(notification)


@router.patch(
    "/{notification_id}/unread",
    response_model=NotificationResponse,
)
async def mark_notification_unread(
    notification_id: UUID,
    current_user: CurrentUser,
    service: NotificationServiceDependency,
) -> NotificationResponse:
    try:
        notification = await service.mark_unread(
            user=current_user,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except NotificationPersistenceError as exc:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    return NotificationResponse.model_validate(notification)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_notification(
    notification_id: UUID,
    current_user: CurrentUser,
    service: NotificationServiceDependency,
) -> Response:
    try:
        await service.delete(
            user=current_user,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except NotificationPersistenceError as exc:
        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
