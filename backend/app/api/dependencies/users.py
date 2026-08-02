from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.users import UserService

DbSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


def get_user_service(
    session: DbSession,
) -> UserService:
    return UserService(
        session=session,
    )


UserServiceDependency = Annotated[
    UserService,
    Depends(get_user_service),
]
