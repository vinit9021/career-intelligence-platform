from typing import Any

import pytest
from httpx2 import AsyncClient


async def register_user(
    client: AsyncClient,
    *,
    email: str = "alice@example.com",
    full_name: str = "Alice Example",
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword9!",
            "full_name": full_name,
        },
    )

    assert response.status_code == 201

    data: dict[str, Any] = response.json()
    return data


def authorization_headers(
    registration: dict[str, Any],
) -> dict[str, str]:
    return {"Authorization": ("Bearer " + str(registration["access_token"]))}


@pytest.mark.asyncio
async def test_current_user_can_be_read_and_updated(
    auth_client: AsyncClient,
) -> None:
    registration = await register_user(auth_client)

    headers = authorization_headers(registration)

    read_response = await auth_client.get(
        "/api/v1/users/me",
        headers=headers,
    )

    assert read_response.status_code == 200
    assert read_response.json()["email"] == "alice@example.com"

    update_response = await auth_client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={
            "email": "Alice.New@Example.com",
            "full_name": " Alice   Updated ",
        },
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["email"] == "alice.new@example.com"
    assert body["full_name"] == "Alice Updated"

    no_change_response = await auth_client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={
            "email": None,
        },
    )

    assert no_change_response.status_code == 200
    assert no_change_response.json()["email"] == "alice.new@example.com"


@pytest.mark.asyncio
async def test_duplicate_user_email_is_rejected(
    auth_client: AsyncClient,
) -> None:
    alice = await register_user(
        auth_client,
        email="alice@example.com",
    )

    await register_user(
        auth_client,
        email="bob@example.com",
        full_name="Bob Example",
    )

    response = await auth_client.patch(
        "/api/v1/users/me",
        headers=authorization_headers(alice),
        json={
            "email": "bob@example.com",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": ("An account with this email address already exists.")}


@pytest.mark.asyncio
async def test_profile_crud_lifecycle(
    auth_client: AsyncClient,
) -> None:
    registration = await register_user(auth_client)

    headers = authorization_headers(registration)

    create_response = await auth_client.post(
        "/api/v1/users/me/profile",
        headers=headers,
        json={
            "headline": ("Backend and AI Engineer"),
            "location": "India",
            "phone": "+91 9876543210",
            "bio": ("Building production AI systems."),
            "years_experience": 3,
            "target_roles": [
                "Backend Engineer",
                "backend engineer",
                "AI Engineer",
            ],
            "skills": [
                "Python",
                "python",
                "FastAPI",
                "PostgreSQL",
            ],
            "linkedin_url": ("https://www.linkedin.com/in/alice"),
            "github_url": ("https://github.com/alice"),
        },
    )

    assert create_response.status_code == 201

    created_profile = create_response.json()

    assert created_profile["target_roles"] == [
        "Backend Engineer",
        "AI Engineer",
    ]

    assert created_profile["skills"] == [
        "Python",
        "FastAPI",
        "PostgreSQL",
    ]

    duplicate_response = await auth_client.post(
        "/api/v1/users/me/profile",
        headers=headers,
        json={},
    )

    assert duplicate_response.status_code == 409

    read_response = await auth_client.get(
        "/api/v1/users/me/profile",
        headers=headers,
    )

    assert read_response.status_code == 200
    assert read_response.json()["headline"] == "Backend and AI Engineer"

    update_response = await auth_client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={
            "headline": ("Senior Backend Engineer"),
            "bio": None,
            "years_experience": 4,
            "skills": None,
        },
    )

    assert update_response.status_code == 200

    updated_profile = update_response.json()

    assert updated_profile["headline"] == "Senior Backend Engineer"
    assert updated_profile["bio"] is None
    assert updated_profile["years_experience"] == 4
    assert updated_profile["skills"] == []

    delete_response = await auth_client.delete(
        "/api/v1/users/me/profile",
        headers=headers,
    )

    assert delete_response.status_code == 204

    missing_read_response = await auth_client.get(
        "/api/v1/users/me/profile",
        headers=headers,
    )

    assert missing_read_response.status_code == 404

    missing_update_response = await auth_client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={
            "headline": "Missing Profile",
        },
    )

    assert missing_update_response.status_code == 404

    missing_delete_response = await auth_client.delete(
        "/api/v1/users/me/profile",
        headers=headers,
    )

    assert missing_delete_response.status_code == 404


@pytest.mark.asyncio
async def test_profile_and_user_validation(
    auth_client: AsyncClient,
) -> None:
    registration = await register_user(auth_client)

    headers = authorization_headers(registration)

    empty_user_update = await auth_client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={},
    )

    invalid_profile = await auth_client.post(
        "/api/v1/users/me/profile",
        headers=headers,
        json={
            "years_experience": 100,
        },
    )

    empty_profile_update = await auth_client.patch(
        "/api/v1/users/me/profile",
        headers=headers,
        json={},
    )

    assert empty_user_update.status_code == 422
    assert invalid_profile.status_code == 422
    assert empty_profile_update.status_code == 422


@pytest.mark.asyncio
async def test_current_user_can_delete_account(
    auth_client: AsyncClient,
) -> None:
    registration = await register_user(auth_client)

    headers = authorization_headers(registration)

    delete_response = await auth_client.delete(
        "/api/v1/users/me",
        headers=headers,
    )

    assert delete_response.status_code == 204

    me_response = await auth_client.get(
        "/api/v1/auth/me",
        headers=headers,
    )

    assert me_response.status_code == 401
