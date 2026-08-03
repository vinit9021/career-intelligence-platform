from pathlib import Path
from typing import Literal

import pytest
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.models import Resume, User
from app.services.resumes import (
    ResumePersistenceError,
    ResumeService,
    ResumeStorageUnavailableError,
)
from app.storage import (
    LocalStorage,
    StorageOperationError,
    StoredFile,
)

SessionFactory = async_sessionmaker[AsyncSession]


async def create_user(
    session: AsyncSession,
) -> User:
    user = User(
        email="alice@example.com",
        password_hash=("stored-password-hash"),
        full_name="Alice Example",
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@pytest.mark.asyncio
async def test_resume_service_uploads_and_persists(
    test_session_factory: SessionFactory,
    tmp_path: Path,
) -> None:
    async with test_session_factory() as session:
        user = await create_user(session)

        storage = LocalStorage(tmp_path / "storage")

        service = ResumeService(
            session=session,
            storage=storage,
            max_size_bytes=1024,
        )

        resume = await service.upload(
            user=user,
            filename="resume.pdf",
            content_type="application/pdf",
            data=b"%PDF-1.7\nresume",
        )

        persisted = await session.get(
            Resume,
            resume.id,
        )

        assert persisted is not None
        assert persisted.user_id == user.id
        assert persisted.storage_backend == "local"

        stored_path = storage.root / Path(*resume.storage_key.split("/"))

        assert stored_path.exists()


class FailingStorage:
    name: Literal["local"] = "local"

    async def save(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
        checksum_sha256: str,
    ) -> StoredFile:
        _ = (
            key,
            data,
            content_type,
            checksum_sha256,
        )

        raise StorageOperationError("storage failed")

    async def delete(
        self,
        *,
        key: str,
    ) -> None:
        _ = key


@pytest.mark.asyncio
async def test_storage_failure_is_wrapped(
    test_session_factory: SessionFactory,
) -> None:
    async with test_session_factory() as session:
        user = await create_user(session)

        service = ResumeService(
            session=session,
            storage=FailingStorage(),
            max_size_bytes=1024,
        )

        with pytest.raises(ResumeStorageUnavailableError):
            await service.upload(
                user=user,
                filename="resume.pdf",
                content_type=("application/pdf"),
                data=b"%PDF-1.7\nresume",
            )


@pytest.mark.asyncio
async def test_file_is_removed_when_database_fails(
    test_session_factory: SessionFactory,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    async with test_session_factory() as session:
        user = await create_user(session)

        storage = LocalStorage(tmp_path / "storage")

        service = ResumeService(
            session=session,
            storage=storage,
            max_size_bytes=1024,
        )

        async def fail_commit() -> None:
            raise RuntimeError("database failed")

        monkeypatch.setattr(
            session,
            "commit",
            fail_commit,
        )

        with pytest.raises(ResumePersistenceError):
            await service.upload(
                user=user,
                filename="resume.pdf",
                content_type=("application/pdf"),
                data=b"%PDF-1.7\nresume",
            )

        stored_files = [path for path in (storage.root.rglob("*")) if path.is_file()]

        assert stored_files == []
