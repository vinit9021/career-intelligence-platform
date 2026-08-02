from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.dependencies.auth import get_current_user
from app.api.v1.auth import login, refresh_tokens, register
from app.core.config import Settings
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.security.tokens import create_access_token
from app.services.auth import (
    AuthService,
    EmailAlreadyRegisteredError,
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
        }
    )


def build_service_mock() -> tuple[MagicMock, AuthService]:
    service_mock = MagicMock(spec=AuthService)

    return service_mock, cast(
        AuthService,
        service_mock,
    )


@pytest.mark.asyncio
async def test_register_converts_duplicate_email_error() -> None:
    service_mock, service = build_service_mock()

    service_mock.register = AsyncMock(side_effect=EmailAlreadyRegisteredError())

    with pytest.raises(HTTPException) as error:
        await register(
            RegisterRequest(
                email="alice@example.com",
                password="StrongPassword9!",
                full_name="Alice Example",
            ),
            service,
        )

    assert error.value.status_code == 409
    assert error.value.detail == ("An account with this email address already exists.")


@pytest.mark.asyncio
async def test_login_converts_invalid_credentials_error() -> None:
    service_mock, service = build_service_mock()

    service_mock.login = AsyncMock(side_effect=InvalidCredentialsError())

    with pytest.raises(HTTPException) as error:
        await login(
            LoginRequest(
                email="alice@example.com",
                password="WrongPassword9!",
            ),
            service,
        )

    assert error.value.status_code == 401
    assert error.value.detail == ("Email or password is incorrect.")
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
async def test_login_converts_inactive_user_error() -> None:
    service_mock, service = build_service_mock()

    service_mock.login = AsyncMock(side_effect=InactiveUserError())

    with pytest.raises(HTTPException) as error:
        await login(
            LoginRequest(
                email="alice@example.com",
                password="StrongPassword9!",
            ),
            service,
        )

    assert error.value.status_code == 403
    assert error.value.detail == ("The user account is inactive.")


@pytest.mark.asyncio
async def test_refresh_converts_invalid_token_error() -> None:
    service_mock, service = build_service_mock()

    service_mock.refresh = AsyncMock(side_effect=InvalidRefreshTokenError())

    with pytest.raises(HTTPException) as error:
        await refresh_tokens(
            RefreshTokenRequest(refresh_token="invalid-refresh-token-value"),
            service,
        )

    assert error.value.status_code == 401
    assert error.value.detail == ("Refresh token is invalid, expired, or already used.")
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
async def test_refresh_converts_inactive_user_error() -> None:
    service_mock, service = build_service_mock()

    service_mock.refresh = AsyncMock(side_effect=InactiveUserError())

    with pytest.raises(HTTPException) as error:
        await refresh_tokens(
            RefreshTokenRequest(refresh_token="inactive-user-refresh-token"),
            service,
        )

    assert error.value.status_code == 403
    assert error.value.detail == ("The user account is inactive.")


@pytest.mark.asyncio
async def test_current_user_rejects_missing_database_user() -> None:
    settings = build_settings()
    user_id = uuid4()

    access_token = create_access_token(
        user_id,
        settings,
    )

    service_mock, service = build_service_mock()
    service_mock.get_user_by_id = AsyncMock(return_value=None)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token.value,
    )

    with pytest.raises(HTTPException) as error:
        await get_current_user(
            credentials,
            service,
            settings,
        )

    assert error.value.status_code == 401
    assert error.value.detail == ("Authentication credentials are invalid or missing.")

    service_mock.get_user_by_id.assert_awaited_once_with(user_id)


@pytest.mark.asyncio
async def test_current_user_rejects_inactive_database_user() -> None:
    settings = build_settings()
    user_id = uuid4()

    access_token = create_access_token(
        user_id,
        settings,
    )

    inactive_user = User(
        id=user_id,
        email="inactive@example.com",
        password_hash="stored-password-hash",
        full_name="Inactive User",
        is_active=False,
        is_verified=False,
    )

    service_mock, service = build_service_mock()
    service_mock.get_user_by_id = AsyncMock(return_value=inactive_user)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=access_token.value,
    )

    with pytest.raises(HTTPException) as error:
        await get_current_user(
            credentials,
            service,
            settings,
        )

    assert error.value.status_code == 403
    assert error.value.detail == ("The user account is inactive.")

    service_mock.get_user_by_id.assert_awaited_once_with(user_id)
