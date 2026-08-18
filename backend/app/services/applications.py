from datetime import UTC, datetime, time
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models import (
    Application,
    User,
)
from app.models.application_timeline import (
    ApplicationTimelineEvent,
)
from app.models.notification import Notification
from app.repositories.application_timeline import (
    ApplicationTimelineRepository,
)
from app.repositories.applications import (
    ApplicationRepository,
)
from app.repositories.notifications import (
    NotificationRepository,
)
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationSortField,
    ApplicationStatus,
    ApplicationUpdateRequest,
    SortOrder,
)


class ApplicationNotFoundError(LookupError):
    pass


class ApplicationPersistenceError(RuntimeError):
    pass


class ApplicationService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        repository: (ApplicationRepository | None) = None,
        timeline_repository: ApplicationTimelineRepository | None = None,
        notification_repository: NotificationRepository | None = None,
    ) -> None:
        self._session = session

        self._notification_repository = notification_repository

        self._timeline_repository = timeline_repository

        self._repository = repository if repository is not None else ApplicationRepository(session)

    async def create(
        self,
        *,
        user: User,
        payload: (ApplicationCreateRequest),
        source: str = "manual",
        external_id: str | None = None,
    ) -> Application:
        data: dict[str, Any] = payload.model_dump()

        job_url = data.get("job_url")

        if job_url is not None:
            data["job_url"] = str(job_url)

        application = Application(
            id=uuid4(),
            user_id=user.id,
            source=source,
            external_id=external_id,
            **data,
        )

        self._repository.add(application)

        try:
            # DAY25_APPLICATION_CREATED_EVENT
            if self._timeline_repository is not None:
                timeline_source = (
                    source
                    if source
                    in {
                        "gmail",
                        "integration",
                    }
                    else "system"
                )

                self._timeline_repository.add(
                    ApplicationTimelineEvent(
                        application_id=application.id,
                        user_id=user.id,
                        event_type="application_submitted",
                        title="Application submitted",
                        description=("Application added to Career Intelligence."),
                        related_status=payload.status,
                        source=timeline_source,
                        event_at=datetime.combine(
                            payload.applied_at,
                            time.min,
                            tzinfo=UTC,
                        ),
                    )
                )

            # DAY27_APPLICATION_NOTIFICATION
            if self._notification_repository is not None:
                self._notification_repository.add(
                    Notification(
                        user_id=user.id,
                        application_id=application.id,
                        type="application_update",
                        title="Application added",
                        message=(
                            f"{application.company} - "
                            f"{application.role} was added "
                            f"to your application tracker."
                        ),
                        source="system",
                    )
                )

            await self._session.commit()

            await self._session.refresh(application)
        except Exception as exc:
            await self._session.rollback()

            raise (ApplicationPersistenceError("The application could not be saved.")) from exc

        return application

    async def list_for_user(
        self,
        *,
        user: User,
        search: str | None,
        status: (ApplicationStatus | None),
        sort_by: (ApplicationSortField),
        sort_order: SortOrder,
        page: int,
        page_size: int,
    ) -> tuple[
        list[Application],
        int,
    ]:
        return await self._repository.list_for_user(
            user_id=user.id,
            search=search,
            status=status,
            sort_by=sort_by,
            sort_order=(sort_order),
            page=page,
            page_size=page_size,
        )

    async def get(
        self,
        *,
        user: User,
        application_id: UUID,
    ) -> Application:
        application = await self._repository.get_by_id_for_user(
            application_id=application_id,
            user_id=user.id,
        )

        if application is None:
            raise ApplicationNotFoundError("Application not found.")

        return application

    async def update(
        self,
        *,
        user: User,
        application_id: UUID,
        payload: (ApplicationUpdateRequest),
    ) -> Application:
        application = await self._repository.get_by_id_for_user(
            application_id=(application_id),
            user_id=user.id,
        )

        if application is None:
            raise (ApplicationNotFoundError("Application not found."))

        # DAY25_PREVIOUS_STATUS
        previous_status = application.status

        data: dict[str, Any] = payload.model_dump(exclude_unset=True)

        if "job_url" in data and data["job_url"] is not None:
            data["job_url"] = str(data["job_url"])

        for (
            field_name,
            value,
        ) in data.items():
            setattr(
                application,
                field_name,
                value,
            )

        # DAY25_STATUS_CHANGED_EVENT
        if self._timeline_repository is not None and application.status != previous_status:
            status_label = application.status.replace("_", " ").title()

            self._timeline_repository.add(
                ApplicationTimelineEvent(
                    application_id=application.id,
                    user_id=user.id,
                    event_type="status_changed",
                    title=(f"Status changed to {status_label}"),
                    description=(
                        f"Application status changed "
                        f"from "
                        f"{previous_status.replace('_', ' ').title()} "
                        f"to {status_label}."
                    ),
                    related_status=application.status,
                    source="system",
                    event_at=datetime.now(UTC),
                )
            )

        try:
            # DAY27_STATUS_NOTIFICATION
            if self._notification_repository is not None and application.status != previous_status:
                status_label = application.status.replace("_", " ").title()

                previous_label = previous_status.replace("_", " ").title()

                notification_type = {
                    "online_assessment": "online_assessment",
                    "interview": "interview",
                    "offer": "offer",
                    "rejected": "rejection",
                }.get(
                    application.status,
                    "application_update",
                )

                self._notification_repository.add(
                    Notification(
                        user_id=user.id,
                        application_id=application.id,
                        type=notification_type,
                        title=(f"Application moved to {status_label}"),
                        message=(
                            f"{application.company} - "
                            f"{application.role} changed "
                            f"from {previous_label} "
                            f"to {status_label}."
                        ),
                        source="system",
                    )
                )

            await self._session.commit()

            await self._session.refresh(application)
        except Exception as exc:
            await self._session.rollback()

            raise (ApplicationPersistenceError("The application could not be updated.")) from exc

        return application

    async def delete(
        self,
        *,
        user: User,
        application_id: UUID,
    ) -> None:
        application = await self._repository.get_by_id_for_user(
            application_id=(application_id),
            user_id=user.id,
        )

        if application is None:
            raise (ApplicationNotFoundError("Application not found."))

        await self._repository.delete(application)

        try:
            await self._session.commit()
        except Exception as exc:
            await self._session.rollback()

            raise (ApplicationPersistenceError("The application could not be deleted.")) from exc
