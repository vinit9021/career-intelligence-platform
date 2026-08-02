from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import RefreshToken, User
from app.schemas.auth import LoginRequest
from app.security.tokens import TokenClaims, TokenValidationError
from app.services import auth as auth_module
from app.services.auth import (
    AuthService,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)


def build_settings() -> Settings:
    return Settings.model_validate(
        {
            "app_env": "test",
            "postgres_host": "unused",
            "postgres_db": "unused",
            "postgres_user": "unused",
            "postgres_password": "unused",
            "jwt_access_secret": "a" * 64,
            "jwt_refresh_secret": "b" * 64,
            "jwt_issuer": "test-issuer",
            "jwt_audience": "test-audience",
            "access_token_expire_minutes": 15,
            "refresh_token_expire_days": 7,
        }
    )


def build_session() -> MagicMock:
    session = MagicMock(spec=AsyncSession)

    session.scalar = AsyncMock()
    session.get = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()

    return session


def build_user(
    *,
    is_active: bool = True,
) -> User:
    now = datetime.now(UTC)

    return User(
        id=uuid4(),
        email="alice@example.com",
        password_hash="stored-password-hash",
        full_name="Alice Example",
        is_active=is_active,
        is_verified=False,
        created_at=now,
        updated_at=now,
    )


def build_claims(
    settings: Settings,
    user_id: UUID,
    jti: UUID,
) -> TokenClaims:
    now = datetime.now(UTC)

    return TokenClaims(
        sub=user_id,
        jti=jti,
        type="refresh",
        iat=now,
        nbf=now,
        exp=now + timedelta(days=7),
        iss=settings.jwt_issuer,
        aud=settings.jwt_audience,
    )


def build_service(
    session: MagicMock,
    settings: Settings | None = None,
) -> AuthService:
    return AuthService(
        session=cast(AsyncSession, session),
        settings=settings or build_settings(),
    )


@pytest.mark.asyncio
async def test_login_rejects_unknown_user(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    session.scalar.return_value = None

    def reject_password(
        password: str,
        password_hash: str,
    ) -> tuple[bool, str | None]:
        return False, None

    monkeypatch.setattr(
        auth_module,
        "verify_and_update_password",
        reject_password,
    )

    service = build_service(session)

    with pytest.raises(InvalidCredentialsError):
        await service.login(
            LoginRequest(
                email="missing@example.com",
                password="StrongPassword9!",
            )
        )


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    session.scalar.return_value = build_user()

    def reject_password(
        password: str,
        password_hash: str,
    ) -> tuple[bool, str | None]:
        return False, None

    monkeypatch.setattr(
        auth_module,
        "verify_and_update_password",
        reject_password,
    )

    service = build_service(session)

    with pytest.raises(InvalidCredentialsError):
        await service.login(
            LoginRequest(
                email="alice@example.com",
                password="WrongPassword9!",
            )
        )


@pytest.mark.asyncio
async def test_login_rejects_inactive_user(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    session.scalar.return_value = build_user(is_active=False)

    def accept_password(
        password: str,
        password_hash: str,
    ) -> tuple[bool, str | None]:
        return True, None

    monkeypatch.setattr(
        auth_module,
        "verify_and_update_password",
        accept_password,
    )

    service = build_service(session)

    with pytest.raises(InactiveUserError):
        await service.login(
            LoginRequest(
                email="alice@example.com",
                password="StrongPassword9!",
            )
        )


@pytest.mark.asyncio
async def test_login_updates_hash_and_issues_tokens(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    user = build_user()
    session.scalar.return_value = user

    def accept_and_upgrade_password(
        password: str,
        password_hash: str,
    ) -> tuple[bool, str | None]:
        return True, "upgraded-password-hash"

    monkeypatch.setattr(
        auth_module,
        "verify_and_update_password",
        accept_and_upgrade_password,
    )

    service = build_service(session)

    result = await service.login(
        LoginRequest(
            email="alice@example.com",
            password="StrongPassword9!",
        )
    )

    assert result.user is user
    assert result.access_token
    assert result.refresh_token
    assert result.expires_in == 900
    assert user.password_hash == "upgraded-password-hash"

    session.add.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_rejects_invalid_jwt(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    service = build_service(session)

    def reject_token(
        *args: object,
        **kwargs: object,
    ) -> TokenClaims:
        raise TokenValidationError("Invalid refresh token.")

    monkeypatch.setattr(
        auth_module,
        "decode_token",
        reject_token,
    )

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh("invalid-refresh-token")


@pytest.mark.asyncio
async def test_refresh_rejects_missing_stored_token(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    settings = build_settings()
    user = build_user()
    claims = build_claims(
        settings,
        user.id,
        uuid4(),
    )

    session.scalar.return_value = None

    def return_claims(
        *args: object,
        **kwargs: object,
    ) -> TokenClaims:
        return claims

    monkeypatch.setattr(
        auth_module,
        "decode_token",
        return_claims,
    )

    service = build_service(
        session,
        settings,
    )

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh("unused-refresh-token")


@pytest.mark.asyncio
async def test_refresh_rejects_missing_user(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    settings = build_settings()
    user = build_user()
    token_jti = uuid4()

    claims = build_claims(
        settings,
        user.id,
        token_jti,
    )

    session.scalar.return_value = RefreshToken(
        user_id=user.id,
        jti=token_jti,
        token_hash="a" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    session.get.return_value = None

    def return_claims(
        *args: object,
        **kwargs: object,
    ) -> TokenClaims:
        return claims

    monkeypatch.setattr(
        auth_module,
        "decode_token",
        return_claims,
    )

    service = build_service(
        session,
        settings,
    )

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh("unused-refresh-token")


@pytest.mark.asyncio
async def test_refresh_rejects_inactive_user(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    settings = build_settings()
    user = build_user(is_active=False)
    token_jti = uuid4()

    claims = build_claims(
        settings,
        user.id,
        token_jti,
    )

    session.scalar.return_value = RefreshToken(
        user_id=user.id,
        jti=token_jti,
        token_hash="b" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    session.get.return_value = user

    def return_claims(
        *args: object,
        **kwargs: object,
    ) -> TokenClaims:
        return claims

    monkeypatch.setattr(
        auth_module,
        "decode_token",
        return_claims,
    )

    service = build_service(
        session,
        settings,
    )

    with pytest.raises(InactiveUserError):
        await service.refresh("unused-refresh-token")


@pytest.mark.asyncio
async def test_refresh_revokes_old_token_and_rotates(
    monkeypatch: MonkeyPatch,
) -> None:
    session = build_session()
    settings = build_settings()
    user = build_user()
    token_jti = uuid4()

    claims = build_claims(
        settings,
        user.id,
        token_jti,
    )

    stored_token = RefreshToken(
        user_id=user.id,
        jti=token_jti,
        token_hash="c" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )

    session.scalar.return_value = stored_token
    session.get.return_value = user

    def return_claims(
        *args: object,
        **kwargs: object,
    ) -> TokenClaims:
        return claims

    monkeypatch.setattr(
        auth_module,
        "decode_token",
        return_claims,
    )

    service = build_service(
        session,
        settings,
    )

    result = await service.refresh("unused-refresh-token")

    assert stored_token.revoked_at is not None
    assert result.user is user
    assert result.access_token
    assert result.refresh_token

    session.add.assert_called_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_id_returns_user() -> None:
    session = build_session()
    user = build_user()

    session.get.return_value = user

    service = build_service(session)

    result = await service.get_user_by_id(user.id)

    assert result is user

    session.get.assert_awaited_once_with(
        User,
        user.id,
    )
