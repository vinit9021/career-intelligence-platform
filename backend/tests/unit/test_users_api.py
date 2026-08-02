from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.users import (
    create_profile,
    delete_current_user,
    delete_profile,
    read_current_user,
    read_profile,
    update_current_user,
    update_profile,
)
from app.models import Profile, User
from app.schemas.users import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    UserUpdateRequest,
)
from app.services.users import (
    EmailAlreadyInUseError,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    UserService,
)


def build_user() -> User:
    now = datetime.now(UTC)

    return User(
        id=uuid4(),
        email="alice@example.com",
        password_hash="stored-password-hash",
        full_name="Alice Example",
        is_active=True,
        is_verified=False,
        created_at=now,
        updated_at=now,
    )


def build_profile(
    user: User,
) -> Profile:
    now = datetime.now(UTC)

    return Profile(
        id=uuid4(),
        user_id=user.id,
        headline="Backend Engineer",
        location="India",
        phone=None,
        bio="Building production systems.",
        years_experience=3,
        target_roles=[
            "Backend Engineer",
        ],
        skills=[
            "Python",
            "FastAPI",
        ],
        linkedin_url=None,
        github_url=None,
        portfolio_url=None,
        created_at=now,
        updated_at=now,
    )


class StubUserService(UserService):
    def __init__(
        self,
        *,
        user: User,
        profile: Profile,
        error: Exception | None = None,
    ) -> None:
        self.result_user = user
        self.result_profile = profile
        self.error = error

    def raise_error_if_present(self) -> None:
        if self.error is not None:
            raise self.error

    async def update_user(
        self,
        user: User,
        payload: UserUpdateRequest,
    ) -> User:
        _ = user, payload

        self.raise_error_if_present()

        return self.result_user

    async def delete_user(
        self,
        user: User,
    ) -> None:
        _ = user

        self.raise_error_if_present()

    async def get_profile(
        self,
        user: User,
    ) -> Profile:
        _ = user

        self.raise_error_if_present()

        return self.result_profile

    async def create_profile(
        self,
        user: User,
        payload: ProfileCreateRequest,
    ) -> Profile:
        _ = user, payload

        self.raise_error_if_present()

        return self.result_profile

    async def update_profile(
        self,
        user: User,
        payload: ProfileUpdateRequest,
    ) -> Profile:
        _ = user, payload

        self.raise_error_if_present()

        return self.result_profile

    async def delete_profile(
        self,
        user: User,
    ) -> None:
        _ = user

        self.raise_error_if_present()


@pytest.mark.asyncio
async def test_user_api_success_handlers() -> None:
    user = build_user()
    profile = build_profile(user)

    service = StubUserService(
        user=user,
        profile=profile,
    )

    read_response = await read_current_user(user)

    assert read_response.id == user.id
    assert str(read_response.email) == "alice@example.com"

    update_response = await update_current_user(
        UserUpdateRequest(
            full_name="Alice Updated",
        ),
        user,
        service,
    )

    assert update_response.id == user.id
    assert str(update_response.email) == "alice@example.com"

    delete_response = await delete_current_user(
        user,
        service,
    )

    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_user_api_converts_duplicate_email_error() -> None:
    user = build_user()
    profile = build_profile(user)

    service = StubUserService(
        user=user,
        profile=profile,
        error=EmailAlreadyInUseError(),
    )

    with pytest.raises(HTTPException) as error:
        await update_current_user(
            UserUpdateRequest(
                email="bob@example.com",
            ),
            user,
            service,
        )

    assert error.value.status_code == 409
    assert error.value.detail == ("An account with this email address already exists.")


@pytest.mark.asyncio
async def test_profile_api_success_handlers() -> None:
    user = build_user()
    profile = build_profile(user)

    service = StubUserService(
        user=user,
        profile=profile,
    )

    create_response = await create_profile(
        ProfileCreateRequest(
            headline="Backend Engineer",
        ),
        user,
        service,
    )

    assert create_response.id == profile.id
    assert create_response.user_id == user.id
    assert create_response.headline == "Backend Engineer"

    read_response = await read_profile(
        user,
        service,
    )

    assert read_response.id == profile.id
    assert read_response.headline == "Backend Engineer"

    update_response = await update_profile(
        ProfileUpdateRequest(
            headline=("Senior Backend Engineer"),
        ),
        user,
        service,
    )

    assert update_response.id == profile.id
    assert update_response.headline == "Backend Engineer"

    delete_response = await delete_profile(
        user,
        service,
    )

    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_profile_api_converts_service_errors() -> None:
    user = build_user()
    profile = build_profile(user)

    duplicate_service = StubUserService(
        user=user,
        profile=profile,
        error=ProfileAlreadyExistsError(),
    )

    with pytest.raises(HTTPException) as duplicate_error:
        await create_profile(
            ProfileCreateRequest(),
            user,
            duplicate_service,
        )

    assert duplicate_error.value.status_code == 409
    assert duplicate_error.value.detail == ("A profile already exists for the current user.")

    not_found_service = StubUserService(
        user=user,
        profile=profile,
        error=ProfileNotFoundError(),
    )

    with pytest.raises(HTTPException) as read_error:
        await read_profile(
            user,
            not_found_service,
        )

    assert read_error.value.status_code == 404
    assert read_error.value.detail == ("Profile not found.")

    with pytest.raises(HTTPException) as update_error:
        await update_profile(
            ProfileUpdateRequest(
                headline="Missing Profile",
            ),
            user,
            not_found_service,
        )

    assert update_error.value.status_code == 404
    assert update_error.value.detail == ("Profile not found.")

    with pytest.raises(HTTPException) as delete_error:
        await delete_profile(
            user,
            not_found_service,
        )

    assert delete_error.value.status_code == 404
    assert delete_error.value.detail == ("Profile not found.")
