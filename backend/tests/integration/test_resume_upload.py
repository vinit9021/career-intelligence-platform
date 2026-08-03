from pathlib import Path
from typing import Any

import pytest
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.models import Resume

SessionFactory = async_sessionmaker[AsyncSession]


async def register_user(
    client: AsyncClient,
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "StrongPassword9!",
            "full_name": "Alice Example",
        },
    )

    assert response.status_code == 201

    data: dict[str, Any] = response.json()

    return data


def auth_headers(
    registration: dict[str, Any],
) -> dict[str, str]:
    return {"Authorization": ("Bearer " + str(registration["access_token"]))}


@pytest.mark.asyncio
async def test_user_can_upload_pdf_resume(
    auth_client: AsyncClient,
    test_session_factory: SessionFactory,
    tmp_path: Path,
) -> None:
    registration = await register_user(auth_client)

    response = await auth_client.post(
        "/api/v1/resume/upload",
        headers=auth_headers(registration),
        files={
            "file": (
                "resume.pdf",
                b"%PDF-1.7\nresume-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["original_filename"] == "resume.pdf"
    assert body["storage_backend"] == "local"
    assert body["file_extension"] == "pdf"
    assert len(body["sha256"]) == 64

    async with test_session_factory() as session:
        resume = await session.scalar(select(Resume))

        assert resume is not None
        assert resume.id.hex == (body["id"].replace("-", ""))

    stored_files = [path for path in (tmp_path / "storage").rglob("*") if path.is_file()]

    assert len(stored_files) == 1


@pytest.mark.asyncio
async def test_invalid_extension_is_rejected(
    auth_client: AsyncClient,
) -> None:
    registration = await register_user(auth_client)

    response = await auth_client.post(
        "/api/v1/resume/upload",
        headers=auth_headers(registration),
        files={
            "file": (
                "resume.txt",
                b"resume",
                "text/plain",
            )
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_oversized_resume_is_rejected(
    auth_client: AsyncClient,
) -> None:
    registration = await register_user(auth_client)

    oversized_data = b"%PDF-" + b"x" * (1024 * 1024)

    response = await auth_client.post(
        "/api/v1/resume/upload",
        headers=auth_headers(registration),
        files={
            "file": (
                "resume.pdf",
                oversized_data,
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_resume_upload_requires_authentication(
    auth_client: AsyncClient,
) -> None:
    response = await auth_client.post(
        "/api/v1/resume/upload",
        files={
            "file": (
                "resume.pdf",
                b"%PDF-1.7\nresume",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 401
