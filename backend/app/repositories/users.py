from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Profile, User


class UserRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        user: User | None = await self._session.scalar(select(User).where(User.email == email))

        return user

    async def delete(
        self,
        user: User,
    ) -> None:
        await self._session.delete(user)


class ProfileRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> Profile | None:
        profile: Profile | None = await self._session.scalar(
            select(Profile).where(Profile.user_id == user_id)
        )

        return profile

    def add(
        self,
        profile: Profile,
    ) -> None:
        self._session.add(profile)

    async def delete(
        self,
        profile: Profile,
    ) -> None:
        await self._session.delete(profile)
