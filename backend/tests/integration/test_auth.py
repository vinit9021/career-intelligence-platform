import pytest
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.models import User

SessionFactory = async_sessionmaker[AsyncSession]

REGISTER_PAYLOAD = {
    "email": "alice@example.com",
    "password": "StrongPassword9!",
    "full_name": "Alice Example",
}


@pytest.mark.asyncio
async def test_register_returns_tokens_and_user(
    auth_client: AsyncClient,
) -> None:
    response = await auth_client.post(
        "/api/v1/auth/register",
        json=REGISTER_PAYLOAD,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert body["access_token"]
    assert body["refresh_token"]

    assert body["user"]["email"] == "alice@example.com"

    assert body["user"]["full_name"] == "Alice Example"

    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


@pytest.mark.asyncio
async def test_duplicate_registration_is_rejected(
    auth_client: AsyncClient,
) -> None:
    first_response = await auth_client.post(
        "/api/v1/auth/register",
        json=REGISTER_PAYLOAD,
    )

    second_response = await auth_client.post(
        "/api/v1/auth/register",
        json=REGISTER_PAYLOAD,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": ("An account with this email address already exists.")
    }


@pytest.mark.asyncio
async def test_login_and_protected_route(
    auth_client: AsyncClient,
) -> None:
    await auth_client.post(
        "/api/v1/auth/register",
        json=REGISTER_PAYLOAD,
    )

    login_response = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": (REGISTER_PAYLOAD["password"]),
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": (f"Bearer {access_token}")},
    )

    assert me_response.status_code == 200

    assert me_response.json()["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_wrong_password_and_missing_token(
    auth_client: AsyncClient,
) -> None:
    await auth_client.post(
        "/api/v1/auth/register",
        json=REGISTER_PAYLOAD,
    )

    login_response = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": "WrongPassword9!",
        },
    )

    me_response = await auth_client.get("/api/v1/auth/me")

    assert login_response.status_code == 401
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation(
    auth_client: AsyncClient,
) -> None:
    register_response = await auth_client.post(
        "/api/v1/auth/register",
        json=REGISTER_PAYLOAD,
    )

    original_refresh_token = register_response.json()["refresh_token"]

    refresh_response = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": (original_refresh_token)},
    )

    assert refresh_response.status_code == 200

    assert refresh_response.json()["refresh_token"] != original_refresh_token

    replay_response = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": (original_refresh_token)},
    )

    assert replay_response.status_code == 401


@pytest.mark.asyncio
async def test_weak_password_is_rejected(
    auth_client: AsyncClient,
) -> None:
    response = await auth_client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "weak-password",
            "full_name": "Weak User",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unknown_user_and_tampered_tokens(
    auth_client: AsyncClient,
) -> None:
    login_response = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "StrongPassword9!",
        },
    )

    refresh_response = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ("tampered-refresh-token-value")},
    )

    me_response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": ("Bearer tampered-access-token")},
    )

    assert login_response.status_code == 401
    assert refresh_response.status_code == 401
    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_is_rejected(
    auth_client: AsyncClient,
    test_session_factory: SessionFactory,
) -> None:
    register_response = await auth_client.post(
        "/api/v1/auth/register",
        json=REGISTER_PAYLOAD,
    )

    access_token = register_response.json()["access_token"]

    refresh_token = register_response.json()["refresh_token"]

    async with test_session_factory() as session:
        user = await session.scalar(select(User).where(User.email == REGISTER_PAYLOAD["email"]))

        assert user is not None

        user.is_active = False
        await session.commit()

    login_response = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": (REGISTER_PAYLOAD["password"]),
        },
    )

    me_response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": (f"Bearer {access_token}")},
    )

    refresh_response = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert login_response.status_code == 403
    assert me_response.status_code == 403
    assert refresh_response.status_code == 403
