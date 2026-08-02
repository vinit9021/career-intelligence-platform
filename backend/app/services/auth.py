from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import RefreshToken, User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
)
from app.security.passwords import (
    hash_password,
    verify_and_update_password,
)
from app.security.tokens import (
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
)

_DUMMY_PASSWORD_HASH = hash_password("DummyPassword9!NeverUsed")


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class InactiveUserError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class AuthResult:
    user: User
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
    ) -> None:
        self._session = session
        self._settings = settings

    async def register(
        self,
        payload: RegisterRequest,
    ) -> AuthResult:
        email = str(payload.email).lower()

        existing_user_id = await self._session.scalar(select(User.id).where(User.email == email))

        if existing_user_id is not None:
            raise EmailAlreadyRegisteredError

        user = User(
            email=email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )

        self._session.add(user)

        try:
            await self._session.flush()
            result = self._issue_token_pair(user)
            await self._session.commit()
            await self._session.refresh(user)
        except IntegrityError as exc:  # pragma: no cover
            await self._session.rollback()
            raise EmailAlreadyRegisteredError from exc
        except Exception:  # pragma: no cover
            await self._session.rollback()
            raise

        return result

    async def login(
        self,
        payload: LoginRequest,
    ) -> AuthResult:
        email = str(payload.email).lower()

        user = await self._session.scalar(select(User).where(User.email == email))

        if user is None:
            verify_and_update_password(
                payload.password,
                _DUMMY_PASSWORD_HASH,
            )
            raise InvalidCredentialsError

        valid_password, updated_hash = verify_and_update_password(
            payload.password,
            user.password_hash,
        )

        if not valid_password:
            raise InvalidCredentialsError

        if not user.is_active:
            raise InactiveUserError

        if updated_hash is not None:
            user.password_hash = updated_hash

        result = self._issue_token_pair(user)

        try:
            await self._session.commit()
        except Exception:  # pragma: no cover
            await self._session.rollback()
            raise

        return result

    async def refresh(
        self,
        raw_refresh_token: str,
    ) -> AuthResult:
        try:
            claims = decode_token(
                raw_refresh_token,
                expected_type="refresh",
                settings=self._settings,
            )
        except TokenValidationError as exc:
            raise InvalidRefreshTokenError from exc

        now = datetime.now(UTC)

        stored_token = await self._session.scalar(
            select(RefreshToken)
            .where(
                RefreshToken.jti == claims.jti,
                RefreshToken.token_hash == hash_token(raw_refresh_token),
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
            .with_for_update()
        )

        if stored_token is None:
            raise InvalidRefreshTokenError

        user = await self._session.get(
            User,
            claims.sub,
        )

        if user is None:
            raise InvalidRefreshTokenError

        if not user.is_active:
            raise InactiveUserError

        stored_token.revoked_at = now

        result = self._issue_token_pair(user)

        try:
            await self._session.commit()
        except Exception:  # pragma: no cover
            await self._session.rollback()
            raise

        return result

    async def get_user_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        return await self._session.get(
            User,
            user_id,
        )

    def _issue_token_pair(
        self,
        user: User,
    ) -> AuthResult:
        access_token = create_access_token(
            user.id,
            self._settings,
        )

        refresh_token = create_refresh_token(
            user.id,
            self._settings,
        )

        self._session.add(
            RefreshToken(
                user_id=user.id,
                jti=refresh_token.jti,
                token_hash=hash_token(refresh_token.value),
                expires_at=refresh_token.expires_at,
            )
        )

        return AuthResult(
            user=user,
            access_token=access_token.value,
            refresh_token=refresh_token.value,
            expires_in=(self._settings.access_token_expire_minutes * 60),
        )
