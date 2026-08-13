from typing import Any
from uuid import UUID

from sqlalchemy import (
    Select,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models import Application


class ApplicationRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    def add(
        self,
        application: Application,
    ) -> None:
        self._session.add(application)

    async def get_by_id_for_user(
        self,
        *,
        application_id: UUID,
        user_id: UUID,
    ) -> Application | None:
        application: Application | None = await self._session.scalar(
            select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )
        )

        return application

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        search: str | None,
        status: str | None,
        sort_by: str,
        sort_order: str,
        page: int,
        page_size: int,
    ) -> tuple[
        list[Application],
        int,
    ]:
        conditions: list[Any] = [Application.user_id == user_id]

        normalized_search = search.strip() if search else ""

        if normalized_search:
            pattern = f"%{normalized_search}%"

            conditions.append(
                or_(
                    Application.company.ilike(pattern),
                    Application.role.ilike(pattern),
                    Application.location.ilike(pattern),
                )
            )

        if status is not None:
            conditions.append(Application.status == status)

        count_statement = select(func.count()).select_from(Application).where(*conditions)

        total_value = await self._session.scalar(count_statement)

        total = int(total_value or 0)

        sort_column: Any

        if sort_by == "company":
            sort_column = Application.company
        elif sort_by == "role":
            sort_column = Application.role
        elif sort_by == "status":
            sort_column = Application.status
        elif sort_by == "created_at":
            sort_column = Application.created_at
        else:
            sort_column = Application.applied_at

        ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()

        statement: Select[tuple[Application]] = (
            select(Application)
            .where(*conditions)
            .order_by(
                ordering,
                Application.created_at.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self._session.scalars(statement)

        return (
            list(result.all()),
            total,
        )

    async def delete(
        self,
        application: Application,
    ) -> None:
        await self._session.delete(application)
