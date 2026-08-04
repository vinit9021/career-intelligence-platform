from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

import pytest
from pytest import MonkeyPatch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import Resume, ResumeParseResult, User
from app.services.resume_library import (
    ResumeDeletePersistenceError,
    ResumeDeleteStorageError,
    ResumeFileUnavailableError,
    ResumeLibraryNotFoundError,
    ResumeLibraryService,
)
from app.storage import LocalStorage, StorageOperationError, StoredFile

SessionFactory = async_sessionmaker[AsyncSession]


async def create_user_and_resume(
    *,
    session: AsyncSession,
    storage: LocalStorage,
    filename: str = "resume.pdf",
) -> tuple[User, Resume, bytes]:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="stored-password-hash",
        full_name="Alice Example",
    )
    session.add(user)
    await session.flush()

    data = b"%PDF-1.7\nresume-content"
    resume_id = uuid4()
    key = f"resumes/{user.id}/{resume_id}/original.pdf"
    await storage.save(
        key=key,
        data=data,
        content_type="application/pdf",
        checksum_sha256="a" * 64,
    )
    resume = Resume(
        id=resume_id,
        user_id=user.id,
        original_filename=filename,
        storage_backend="local",
        storage_key=key,
        storage_etag="a" * 64,
        content_type="application/pdf",
        file_extension="pdf",
        file_size_bytes=len(data),
        sha256="a" * 64,
        parse_status="pending",
        created_at=datetime.now(UTC),
    )
    session.add(resume)
    await session.commit()
    await session.refresh(user)
    await session.refresh(resume)
    return user, resume, data


@pytest.mark.asyncio
async def test_history_detail_status_and_unparsed_viewer(
    test_session_factory: SessionFactory,
    tmp_path: Path,
) -> None:
    async with test_session_factory() as session:
        storage = LocalStorage(tmp_path / "storage")
        user, resume, _ = await create_user_and_resume(
            session=session,
            storage=storage,
        )
        service = ResumeLibraryService(session=session, storage=storage)

        history = await service.list_history(user=user, page=1, page_size=20)
        detail = await service.get_detail(user=user, resume_id=resume.id)
        parse_status = await service.get_parse_status(
            user=user,
            resume_id=resume.id,
        )
        viewer = await service.get_viewer(user=user, resume_id=resume.id)

        assert history.total == 1
        assert history.total_pages == 1
        assert history.items[0].id == resume.id
        assert detail.sha256 == "a" * 64
        assert parse_status.status == "pending"
        assert parse_status.has_parsed_result is False
        assert viewer.content is None
        assert viewer.metadata is None


@pytest.mark.asyncio
async def test_parsed_viewer_and_file(
    test_session_factory: SessionFactory,
    tmp_path: Path,
) -> None:
    async with test_session_factory() as session:
        storage = LocalStorage(tmp_path / "storage")
        user, resume, data = await create_user_and_resume(
            session=session,
            storage=storage,
        )
        result = ResumeParseResult(
            resume_id=resume.id,
            source_type="pdf",
            parser_name="pypdf",
            parser_version="1",
            raw_text="Python FastAPI",
            structured_data={
                "contact": {},
                "summary": "Backend engineer",
                "skills": ["Python", "FastAPI"],
                "education": [],
                "experience": [],
                "projects": [],
                "certifications": [],
            },
            warnings=[],
            page_count=1,
            character_count=14,
            requires_ocr=False,
        )
        resume.parse_status = "completed"
        resume.parsed_at = datetime.now(UTC)
        session.add(result)
        await session.commit()

        service = ResumeLibraryService(session=session, storage=storage)
        viewer = await service.get_viewer(user=user, resume_id=resume.id)
        file_payload = await service.get_file(user=user, resume_id=resume.id)

        assert viewer.content is not None
        assert viewer.content.skills == ["Python", "FastAPI"]
        assert viewer.metadata is not None
        assert viewer.metadata.page_count == 1
        assert file_payload.data == data
        assert file_payload.filename == "resume.pdf"


@pytest.mark.asyncio
async def test_delete_removes_record_and_file(
    test_session_factory: SessionFactory,
    tmp_path: Path,
) -> None:
    async with test_session_factory() as session:
        storage = LocalStorage(tmp_path / "storage")
        user, resume, _ = await create_user_and_resume(
            session=session,
            storage=storage,
        )
        key = resume.storage_key
        service = ResumeLibraryService(session=session, storage=storage)

        response = await service.delete_resume(user=user, resume_id=resume.id)

        assert response.deleted is True
        assert await session.get(Resume, resume.id) is None
        with pytest.raises(StorageOperationError):
            await storage.read(key=key)


@pytest.mark.asyncio
async def test_missing_resume_is_rejected(
    test_session_factory: SessionFactory,
    tmp_path: Path,
) -> None:
    async with test_session_factory() as session:
        storage = LocalStorage(tmp_path / "storage")
        user = User(
            email="missing@example.com",
            password_hash="stored-password-hash",
            full_name="Missing User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        service = ResumeLibraryService(session=session, storage=storage)

        with pytest.raises(ResumeLibraryNotFoundError):
            await service.get_detail(user=user, resume_id=uuid4())

        with pytest.raises(ResumeLibraryNotFoundError):
            await service.get_viewer(user=user, resume_id=uuid4())


class FailingStorage:
    @property
    def name(self) -> Literal["local"]:
        return "local"

    async def save(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
        checksum_sha256: str,
    ) -> StoredFile:
        _ = key, data, content_type, checksum_sha256
        return StoredFile(key=key, etag=None, size_bytes=len(data))

    async def read(self, *, key: str) -> bytes:
        _ = key
        raise StorageOperationError("read failed")

    async def delete(self, *, key: str) -> None:
        _ = key
        raise StorageOperationError("delete failed")


@pytest.mark.asyncio
async def test_storage_failures_are_wrapped(
    test_session_factory: SessionFactory,
    tmp_path: Path,
) -> None:
    async with test_session_factory() as session:
        local = LocalStorage(tmp_path / "storage")
        user, resume, _ = await create_user_and_resume(
            session=session,
            storage=local,
        )
        service = ResumeLibraryService(session=session, storage=FailingStorage())

        with pytest.raises(ResumeFileUnavailableError):
            await service.get_file(user=user, resume_id=resume.id)

        with pytest.raises(ResumeDeleteStorageError):
            await service.delete_resume(user=user, resume_id=resume.id)


@pytest.mark.asyncio
async def test_delete_restores_file_when_database_commit_fails(
    test_session_factory: SessionFactory,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    async with test_session_factory() as session:
        storage = LocalStorage(tmp_path / "storage")
        user, resume, data = await create_user_and_resume(
            session=session,
            storage=storage,
        )
        service = ResumeLibraryService(session=session, storage=storage)
        storage_key = resume.storage_key
        original_commit = session.commit
        calls = 0

        async def fail_once() -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise SQLAlchemyError("database failed")
            await original_commit()

        monkeypatch.setattr(session, "commit", fail_once)

        with pytest.raises(ResumeDeletePersistenceError):
            await service.delete_resume(user=user, resume_id=resume.id)

        restored = await storage.read(key=storage_key)
        assert restored == data
