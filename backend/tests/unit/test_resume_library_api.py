from typing import cast
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.resume_library import delete_resume, download_resume_file
from app.models import User
from app.services.resume_library import (
    ResumeDeletePersistenceError,
    ResumeDeleteStorageError,
    ResumeFileUnavailableError,
    ResumeLibraryService,
)


def build_user() -> User:
    return User(
        id=uuid4(),
        email="api-errors@example.com",
        password_hash="stored-password-hash",
        full_name="API Error User",
    )


class ErrorService:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def get_file(self, **_: object) -> None:
        raise self._error

    async def delete_resume(self, **_: object) -> None:
        raise self._error


@pytest.mark.asyncio
async def test_file_unavailable_maps_to_503() -> None:
    service = cast(
        ResumeLibraryService,
        ErrorService(ResumeFileUnavailableError("unavailable")),
    )

    with pytest.raises(HTTPException) as raised:
        await download_resume_file(
            resume_id=uuid4(),
            current_user=build_user(),
            service=service,
        )

    assert raised.value.status_code == 503


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (ResumeDeleteStorageError("storage failed"), 503),
        (ResumeDeletePersistenceError("database failed"), 500),
    ],
)
async def test_delete_errors_are_mapped(
    error: Exception,
    expected_status: int,
) -> None:
    service = cast(ResumeLibraryService, ErrorService(error))

    with pytest.raises(HTTPException) as raised:
        await delete_resume(
            resume_id=uuid4(),
            current_user=build_user(),
            service=service,
        )

    assert raised.value.status_code == expected_status
