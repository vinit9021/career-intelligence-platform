from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies.auth import (
    AuthServiceDependency,
    CurrentUser,
)
from app.schemas.auth import (
    AuthResponse,
    ErrorResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.auth import (
    AuthResult,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

UNAUTHORIZED_RESPONSE = {
    "model": ErrorResponse,
    "description": "Authentication failed.",
}


def _response_from_result(
    result: AuthResult,
) -> AuthResponse:
    return AuthResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
        user=UserResponse.model_validate(result.user),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": ("The email address is already registered."),
        },
    },
)
async def register(
    payload: RegisterRequest,
    service: AuthServiceDependency,
) -> AuthResponse:
    try:
        result = await service.register(payload)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("An account with this email address already exists."),
        ) from exc

    return _response_from_result(result)


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: (UNAUTHORIZED_RESPONSE),
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": ("The user account is inactive."),
        },
    },
)
async def login(
    payload: LoginRequest,
    service: AuthServiceDependency,
) -> AuthResponse:
    try:
        result = await service.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user account is inactive.",
        ) from exc

    return _response_from_result(result)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: (UNAUTHORIZED_RESPONSE),
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": ("The user account is inactive."),
        },
    },
)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    service: AuthServiceDependency,
) -> AuthResponse:
    try:
        result = await service.refresh(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=("Refresh token is invalid, expired, or already used."),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user account is inactive.",
        ) from exc

    return _response_from_result(result)


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: (UNAUTHORIZED_RESPONSE),
        status.HTTP_403_FORBIDDEN: {
            "model": ErrorResponse,
            "description": ("The user account is inactive."),
        },
    },
)
async def read_current_user(
    current_user: CurrentUser,
) -> UserResponse:
    return UserResponse.model_validate(current_user)
