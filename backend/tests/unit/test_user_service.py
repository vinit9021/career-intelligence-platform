import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.models import User
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


async def create_user(
    session: AsyncSession,
    *,
    email: str = "alice@example.com",
    full_name: str = "Alice Example",
) -> User:
    user = User(
        email=email,
        password_hash="stored-password-hash",
        full_name=full_name,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@pytest.mark.asyncio
async def test_user_can_be_updated_without_changing_null_fields(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        user = await create_user(session)
        service = UserService(session)

        updated_user = await service.update_user(
            user,
            UserUpdateRequest(
                email="Alice.New@Example.com",
                full_name="Alice Updated",
            ),
        )

        assert updated_user.email == "alice.new@example.com"
        assert updated_user.full_name == "Alice Updated"

        unchanged_user = await service.update_user(
            updated_user,
            UserUpdateRequest(
                email=None,
            ),
        )

        assert unchanged_user is updated_user
        assert unchanged_user.email == "alice.new@example.com"


@pytest.mark.asyncio
async def test_duplicate_user_email_is_rejected(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        alice = await create_user(
            session,
            email="alice@example.com",
        )

        await create_user(
            session,
            email="bob@example.com",
            full_name="Bob Example",
        )

        service = UserService(session)

        with pytest.raises(EmailAlreadyInUseError):
            await service.update_user(
                alice,
                UserUpdateRequest(
                    email="bob@example.com",
                ),
            )


@pytest.mark.asyncio
async def test_user_can_be_deleted(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        user = await create_user(session)
        user_id = user.id

        service = UserService(session)

        await service.delete_user(user)

        deleted_user = await session.get(
            User,
            user_id,
        )

        assert deleted_user is None


@pytest.mark.asyncio
async def test_profile_service_lifecycle_and_errors(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_session_factory() as session:
        user = await create_user(session)
        service = UserService(session)

        with pytest.raises(ProfileNotFoundError):
            await service.get_profile(user)

        profile = await service.create_profile(
            user,
            ProfileCreateRequest(
                headline=("Backend and AI Engineer"),
                location="India",
                years_experience=3,
                target_roles=[
                    "Backend Engineer",
                    "AI Engineer",
                ],
                skills=[
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                ],
            ),
        )

        assert profile.user_id == user.id
        assert profile.headline == "Backend and AI Engineer"
        assert profile.years_experience == 3

        fetched_profile = await service.get_profile(user)

        assert fetched_profile.id == profile.id

        with pytest.raises(ProfileAlreadyExistsError):
            await service.create_profile(
                user,
                ProfileCreateRequest(),
            )

        updated_profile = await service.update_profile(
            user,
            ProfileUpdateRequest(
                headline=("Senior Backend Engineer"),
                bio=None,
                years_experience=5,
                skills=None,
            ),
        )

        assert updated_profile.headline == "Senior Backend Engineer"
        assert updated_profile.bio is None
        assert updated_profile.years_experience == 5
        assert updated_profile.skills == []

        await service.delete_profile(user)

        with pytest.raises(ProfileNotFoundError):
            await service.get_profile(user)

        with pytest.raises(ProfileNotFoundError):
            await service.update_profile(
                user,
                ProfileUpdateRequest(
                    headline="Missing Profile",
                ),
            )

        with pytest.raises(ProfileNotFoundError):
            await service.delete_profile(user)
