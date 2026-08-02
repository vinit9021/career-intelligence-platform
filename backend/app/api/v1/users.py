from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
)

from app.api.dependencies import (
    CurrentUser,
    UserServiceDependency,
)
from app.schemas.auth import (
    ErrorResponse,
    UserResponse,
)
from app.schemas.users import (
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    UserUpdateRequest,
)
from app.services.users import (
    EmailAlreadyInUseError,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def read_current_user(
    current_user: CurrentUser,
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": ("The requested email address is already in use."),
        },
    },
)
async def update_current_user(
    payload: UserUpdateRequest,
    current_user: CurrentUser,
    service: UserServiceDependency,
) -> UserResponse:
    try:
        user = await service.update_user(
            current_user,
            payload,
        )
    except EmailAlreadyInUseError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("An account with this email address already exists."),
        ) from exc

    return UserResponse.model_validate(user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_current_user(
    current_user: CurrentUser,
    service: UserServiceDependency,
) -> Response:
    await service.delete_user(current_user)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/me/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": ("A profile already exists for the current user."),
        },
    },
)
async def create_profile(
    payload: ProfileCreateRequest,
    current_user: CurrentUser,
    service: UserServiceDependency,
) -> ProfileResponse:
    try:
        profile = await service.create_profile(
            current_user,
            payload,
        )
    except ProfileAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("A profile already exists for the current user."),
        ) from exc

    return ProfileResponse.model_validate(profile)


@router.get(
    "/me/profile",
    response_model=ProfileResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": ("The current user does not have a profile."),
        },
    },
)
async def read_profile(
    current_user: CurrentUser,
    service: UserServiceDependency,
) -> ProfileResponse:
    try:
        profile = await service.get_profile(current_user)
    except ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        ) from exc

    return ProfileResponse.model_validate(profile)


@router.patch(
    "/me/profile",
    response_model=ProfileResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": ("The current user does not have a profile."),
        },
    },
)
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: CurrentUser,
    service: UserServiceDependency,
) -> ProfileResponse:
    try:
        profile = await service.update_profile(
            current_user,
            payload,
        )
    except ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        ) from exc

    return ProfileResponse.model_validate(profile)


@router.delete(
    "/me/profile",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": ("The current user does not have a profile."),
        },
    },
)
async def delete_profile(
    current_user: CurrentUser,
    service: UserServiceDependency,
) -> Response:
    try:
        await service.delete_profile(current_user)
    except ProfileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
