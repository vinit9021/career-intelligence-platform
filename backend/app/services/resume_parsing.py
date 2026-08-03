import asyncio
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Resume, ResumeParseResult, User
from app.parsers import (
    ResumeParserError,
    ResumeParserRegistry,
    build_structured_resume,
)
from app.repositories.resumes import (
    ResumeParseResultRepository,
    ResumeRepository,
)
from app.schemas.resume_parsing import (
    ResumeParseMetadata,
    ResumeParseResponse,
    ResumeParseStatus,
    ResumeSourceType,
    ResumeStructuredContent,
)
from app.storage import ObjectStorage, StorageError


class ResumeNotFoundError(LookupError):
    pass


class ResumeParseResultNotFoundError(LookupError):
    pass


class ResumeSourceUnavailableError(RuntimeError):
    pass


class ResumeParsingFailedError(RuntimeError):
    pass


class ResumeParsingPersistenceError(RuntimeError):
    pass


class ResumeParsingService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        storage: ObjectStorage,
        parser_registry: ResumeParserRegistry,
        resume_repository: ResumeRepository | None = None,
        result_repository: ResumeParseResultRepository | None = None,
    ) -> None:
        self._session = session
        self._storage = storage
        self._parser_registry = parser_registry
        self._resume_repository = resume_repository or ResumeRepository(session)
        self._result_repository = result_repository or ResumeParseResultRepository(session)

    async def parse_resume(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> ResumeParseResponse:
        resume = await self._get_owned_resume(user=user, resume_id=resume_id)
        resume.parse_status = "processing"
        resume.parse_error = None

        try:
            data = await self._storage.read(key=resume.storage_key)
        except StorageError as exc:
            await self._mark_failed(resume, "The stored resume could not be read.")
            raise ResumeSourceUnavailableError(
                "The stored resume is temporarily unavailable."
            ) from exc

        try:
            parser = self._parser_registry.get(resume.file_extension)
            extracted = await asyncio.to_thread(parser.parse, data)
        except ResumeParserError as exc:
            await self._mark_failed(resume, str(exc))
            raise ResumeParsingFailedError(str(exc)) from exc

        content, metadata = build_structured_resume(
            extracted=extracted,
            source_type=parser.extension,
            parser_name=parser.name,
            parser_version=parser.version,
        )
        result = await self._result_repository.get_by_resume_id(resume.id)

        if result is None:
            result = ResumeParseResult(
                resume_id=resume.id,
                source_type=metadata.source_type,
                parser_name=metadata.parser_name,
                parser_version=metadata.parser_version,
                raw_text=extracted.raw_text,
                structured_data=content.model_dump(mode="json"),
                warnings=metadata.warnings,
                page_count=metadata.page_count,
                character_count=metadata.character_count,
                requires_ocr=metadata.requires_ocr,
            )
            self._result_repository.add(result)
        else:
            result.source_type = metadata.source_type
            result.parser_name = metadata.parser_name
            result.parser_version = metadata.parser_version
            result.raw_text = extracted.raw_text
            result.structured_data = content.model_dump(mode="json")
            result.warnings = metadata.warnings
            result.page_count = metadata.page_count
            result.character_count = metadata.character_count
            result.requires_ocr = metadata.requires_ocr

        parsed_at = datetime.now(UTC)
        resume.parse_status = "needs_ocr" if metadata.requires_ocr else "completed"
        resume.parse_error = None
        resume.parsed_at = parsed_at

        try:
            await self._session.commit()
            await self._session.refresh(result)
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise ResumeParsingPersistenceError(
                "The parsed resume could not be persisted."
            ) from exc

        return self._build_response(
            resume=resume,
            result=result,
            content=content,
            metadata=metadata,
            parsed_at=parsed_at,
        )

    async def get_parse_result(
        self,
        *,
        user: User,
        resume_id: UUID,
    ) -> ResumeParseResponse:
        resume = await self._get_owned_resume(user=user, resume_id=resume_id)
        result = await self._result_repository.get_by_resume_id(resume.id)

        if result is None:
            raise ResumeParseResultNotFoundError("The resume has not been parsed yet.")

        content = ResumeStructuredContent.model_validate(result.structured_data)
        metadata = ResumeParseMetadata(
            source_type=cast(ResumeSourceType, result.source_type),
            parser_name=result.parser_name,
            parser_version=result.parser_version,
            page_count=result.page_count,
            character_count=result.character_count,
            requires_ocr=result.requires_ocr,
            warnings=result.warnings,
        )
        parsed_at = resume.parsed_at or result.updated_at

        return self._build_response(
            resume=resume,
            result=result,
            content=content,
            metadata=metadata,
            parsed_at=parsed_at,
        )

    async def _get_owned_resume(self, *, user: User, resume_id: UUID) -> Resume:
        resume = await self._resume_repository.get_by_id_for_user(
            resume_id=resume_id,
            user_id=user.id,
        )

        if resume is None:
            raise ResumeNotFoundError("Resume not found.")

        return resume

    async def _mark_failed(self, resume: Resume, message: str) -> None:
        resume.parse_status = "failed"
        resume.parse_error = message[:1000]
        resume.parsed_at = None

        try:
            await self._session.commit()
        except SQLAlchemyError:
            await self._session.rollback()

    @staticmethod
    def _build_response(
        *,
        resume: Resume,
        result: ResumeParseResult,
        content: ResumeStructuredContent,
        metadata: ResumeParseMetadata,
        parsed_at: datetime,
    ) -> ResumeParseResponse:
        status: ResumeParseStatus = "needs_ocr" if metadata.requires_ocr else "completed"

        return ResumeParseResponse(
            id=result.id,
            resume_id=resume.id,
            status=status,
            content=content,
            raw_text=result.raw_text,
            metadata=metadata,
            parsed_at=parsed_at,
        )
