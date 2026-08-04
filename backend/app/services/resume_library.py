from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Resume, ResumeParseResult, User
from app.repositories.resume_library import ResumeLibraryRepository
from app.schemas.resume_library import (
    ResumeDeleteResponse,
    ResumeDetailResponse,
    ResumeFileExtension,
    ResumeHistoryItem,
    ResumeHistoryPage,
    ResumeLifecycleStatus,
    ResumeParseStatusResponse,
    ResumeStorageBackend,
    ResumeViewerResponse,
)
from app.schemas.resume_parsing import (
    ResumeParseMetadata,
    ResumeSourceType,
    ResumeStructuredContent,
)
from app.storage import ObjectStorage, StorageError


class ResumeLibraryNotFoundError(LookupError):
    pass


class ResumeFileUnavailableError(RuntimeError):
    pass


class ResumeDeleteStorageError(RuntimeError):
    pass


class ResumeDeletePersistenceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ResumeFilePayload:
    data: bytes
    filename: str
    content_type: str
    sha256: str


class ResumeLibraryService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        storage: ObjectStorage,
        repository: ResumeLibraryRepository | None = None,
    ) -> None:
        self._session = session
        self._storage = storage
        self._repository = repository or ResumeLibraryRepository(session)

    async def list_history(
        self,
        *,
        user: User,
        page: int,
        page_size: int,
    ) -> ResumeHistoryPage:
        total = await self._repository.count_for_user(user.id)
        offset = (page - 1) * page_size
        resumes = await self._repository.list_for_user(
            user_id=user.id,
            offset=offset,
            limit=page_size,
        )
        total_pages = (total + page_size - 1) // page_size if total else 0

        return ResumeHistoryPage(
            items=[self._history_item(resume) for resume in resumes],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    async def get_detail(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> ResumeDetailResponse:
        resume = await self._get_owned_resume(user=user, resume_id=resume_id)
        return self._detail(resume)

    async def get_parse_status(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> ResumeParseStatusResponse:
        resume = await self._get_owned_resume_with_result(
            user=user,
            resume_id=resume_id,
        )
        return ResumeParseStatusResponse(
            resume_id=resume.id,
            status=cast(ResumeLifecycleStatus, resume.parse_status),
            error=resume.parse_error,
            parsed_at=resume.parsed_at,
            has_parsed_result=resume.parse_result is not None,
        )

    async def get_viewer(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> ResumeViewerResponse:
        resume = await self._get_owned_resume_with_result(
            user=user,
            resume_id=resume_id,
        )
        result = resume.parse_result

        if result is None:
            return ResumeViewerResponse(
                resume=self._detail(resume),
                content=None,
                raw_text=None,
                metadata=None,
            )

        return ResumeViewerResponse(
            resume=self._detail(resume),
            content=ResumeStructuredContent.model_validate(result.structured_data),
            raw_text=result.raw_text,
            metadata=self._parse_metadata(result),
        )

    async def get_file(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> ResumeFilePayload:
        resume = await self._get_owned_resume(user=user, resume_id=resume_id)

        try:
            data = await self._storage.read(key=resume.storage_key)
        except StorageError as exc:
            raise ResumeFileUnavailableError(
                "The stored resume is temporarily unavailable."
            ) from exc

        return ResumeFilePayload(
            data=data,
            filename=resume.original_filename,
            content_type=resume.content_type,
            sha256=resume.sha256,
        )

    async def delete_resume(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> ResumeDeleteResponse:
        resume = await self._get_owned_resume(user=user, resume_id=resume_id)

        storage_key = resume.storage_key
        content_type = resume.content_type
        checksum_sha256 = resume.sha256

        try:
            backup_data = await self._storage.read(key=storage_key)
            await self._storage.delete(key=storage_key)
        except StorageError as exc:
            raise ResumeDeleteStorageError("The stored resume could not be deleted.") from exc

        await self._repository.delete(resume)

        try:
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()

            try:
                await self._storage.save(
                    key=storage_key,
                    data=backup_data,
                    content_type=content_type,
                    checksum_sha256=checksum_sha256,
                )
            except StorageError:
                pass

            raise ResumeDeletePersistenceError("The resume record could not be deleted.") from exc

        return ResumeDeleteResponse(resume_id=resume_id)

    async def _get_owned_resume(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> Resume:
        resume = await self._repository.get_by_id_for_user(
            resume_id=resume_id,
            user_id=user.id,
        )

        if resume is None:
            raise ResumeLibraryNotFoundError("Resume not found.")

        return resume

    async def _get_owned_resume_with_result(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> Resume:
        resume = await self._repository.get_with_parse_result_for_user(
            resume_id=resume_id,
            user_id=user.id,
        )

        if resume is None:
            raise ResumeLibraryNotFoundError("Resume not found.")

        return resume

    @staticmethod
    def _history_item(resume: Resume) -> ResumeHistoryItem:
        return ResumeHistoryItem(
            id=resume.id,
            original_filename=resume.original_filename,
            content_type=resume.content_type,
            file_extension=cast(ResumeFileExtension, resume.file_extension),
            file_size_bytes=resume.file_size_bytes,
            storage_backend=cast(ResumeStorageBackend, resume.storage_backend),
            parse_status=cast(ResumeLifecycleStatus, resume.parse_status),
            parsed_at=resume.parsed_at,
            created_at=resume.created_at,
        )

    @classmethod
    def _detail(cls, resume: Resume) -> ResumeDetailResponse:
        item = cls._history_item(resume)
        return ResumeDetailResponse(
            **item.model_dump(),
            sha256=resume.sha256,
            parse_error=resume.parse_error,
        )

    @staticmethod
    def _parse_metadata(result: ResumeParseResult) -> ResumeParseMetadata:
        return ResumeParseMetadata(
            source_type=cast(ResumeSourceType, result.source_type),
            parser_name=result.parser_name,
            parser_version=result.parser_version,
            page_count=result.page_count,
            character_count=result.character_count,
            requires_ocr=result.requires_ocr,
            warnings=result.warnings,
        )
