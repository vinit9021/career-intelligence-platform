from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile, User
from app.repositories import (
    ProfileRepository,
    UserRepository,
)
from app.schemas.users import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    UserUpdateRequest,
)


class EmailAlreadyInUseError(Exception):
    pass


class ProfileAlreadyExistsError(Exception):
    pass


class ProfileNotFoundError(Exception):
    pass


class UserService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository | None = None,
        profile_repository: ProfileRepository | None = None,
    ) -> None:
        self._session = session

        self._users = user_repository if user_repository is not None else UserRepository(session)

        self._profiles = (
            profile_repository if profile_repository is not None else ProfileRepository(session)
        )

    async def update_user(
        self,
        user: User,
        payload: UserUpdateRequest,
    ) -> User:
        data = payload.model_dump(
            mode="json",
            exclude_unset=True,
        )

        data = {name: value for name, value in data.items() if value is not None}

        if not data:
            return user

        email = data.get("email")

        if isinstance(email, str):
            normalized_email = email.lower()

            existing_user = await self._users.get_by_email(normalized_email)

            if existing_user is not None and existing_user.id != user.id:
                raise EmailAlreadyInUseError

            data["email"] = normalized_email

        for field_name, value in data.items():
            setattr(
                user,
                field_name,
                value,
            )

        try:
            await self._session.commit()
            await self._session.refresh(user)
        except IntegrityError as exc:
            await self._session.rollback()
            raise EmailAlreadyInUseError from exc
        except Exception:  # pragma: no cover
            await self._session.rollback()
            raise

        return user

    async def delete_user(
        self,
        user: User,
    ) -> None:
        await self._users.delete(user)

        try:
            await self._session.commit()
        except Exception:  # pragma: no cover
            await self._session.rollback()
            raise

    async def get_profile(
        self,
        user: User,
    ) -> Profile:
        profile = await self._profiles.get_by_user_id(user.id)

        if profile is None:
            raise ProfileNotFoundError

        return profile

    async def create_profile(
        self,
        user: User,
        payload: ProfileCreateRequest,
    ) -> Profile:
        existing_profile = await self._profiles.get_by_user_id(user.id)

        if existing_profile is not None:
            raise ProfileAlreadyExistsError

        data = payload.model_dump(
            mode="json",
        )

        profile = Profile(
            user_id=user.id,
            **data,
        )

        self._profiles.add(profile)

        try:
            await self._session.commit()
            await self._session.refresh(profile)
        except IntegrityError as exc:
            await self._session.rollback()
            raise ProfileAlreadyExistsError from exc
        except Exception:  # pragma: no cover
            await self._session.rollback()
            raise

        return profile

    async def update_profile(
        self,
        user: User,
        payload: ProfileUpdateRequest,
    ) -> Profile:
        profile = await self._profiles.get_by_user_id(user.id)

        if profile is None:
            raise ProfileNotFoundError

        data = payload.model_dump(
            mode="json",
            exclude_unset=True,
        )

        for list_field in (
            "target_roles",
            "skills",
        ):
            if list_field in data and data[list_field] is None:
                data[list_field] = []

        for field_name, value in data.items():
            setattr(
                profile,
                field_name,
                value,
            )

        try:
            await self._session.commit()
            await self._session.refresh(profile)
        except Exception:  # pragma: no cover
            await self._session.rollback()
            raise

        return profile

    async def delete_profile(
        self,
        user: User,
    ) -> None:
        profile = await self._profiles.get_by_user_id(user.id)

        if profile is None:
            raise ProfileNotFoundError

        await self._profiles.delete(profile)

        try:
            await self._session.commit()
        except Exception:  # pragma: no cover
            await self._session.rollback()
            raise
