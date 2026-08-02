from typing import Annotated

from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models import User
from app.security.tokens import (
    TokenValidationError,
    decode_token,
)
from app.services.auth import AuthService

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="JWT bearer",
    description="Enter a valid JWT access token.",
)

DbSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]

SettingsDependency = Annotated[
    Settings,
    Depends(get_settings),
]

BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def get_auth_service(
    session: DbSession,
    settings: SettingsDependency,
) -> AuthService:
    return AuthService(
        session=session,
        settings=settings,
    )


AuthServiceDependency = Annotated[
    AuthService,
    Depends(get_auth_service),
]


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=("Authentication credentials are invalid or missing."),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: BearerCredentials,
    service: AuthServiceDependency,
    settings: SettingsDependency,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized_exception()

    try:
        claims = decode_token(
            credentials.credentials,
            expected_type="access",
            settings=settings,
        )
    except TokenValidationError as exc:
        raise _unauthorized_exception() from exc

    user = await service.get_user_by_id(claims.sub)

    if user is None:
        raise _unauthorized_exception()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user account is inactive.",
        )

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]
