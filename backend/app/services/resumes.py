from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from typing import Literal
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models import Resume, User
from app.repositories import ResumeRepository
from app.storage import (
    ObjectStorage,
    StorageError,
)

ResumeExtension = Literal[
    "pdf",
    "docx",
]


@dataclass(
    frozen=True,
    slots=True,
)
class ValidatedResumeUpload:
    original_filename: str
    extension: ResumeExtension
    content_type: str
    data: bytes
    sha256: str


class InvalidResumeError(ValueError):
    pass


class ResumeTooLargeError(InvalidResumeError):
    pass


class ResumeStorageUnavailableError(RuntimeError):
    pass


class ResumePersistenceError(RuntimeError):
    pass


def _safe_filename(
    filename: str,
) -> str:
    normalized = filename.replace("\\", "/").strip()

    safe_name = PurePosixPath(normalized).name.strip()

    if not safe_name:
        raise InvalidResumeError("The uploaded file must have a filename.")

    if len(safe_name) > 255:
        raise InvalidResumeError("The filename must not exceed 255 characters.")

    return safe_name


def _validate_pdf(
    data: bytes,
) -> None:
    if not data.startswith(b"%PDF-"):
        raise InvalidResumeError("The uploaded file is not a valid PDF document.")


def _validate_docx(
    data: bytes,
) -> None:
    required_members = {
        "[Content_Types].xml",
        "word/document.xml",
    }

    try:
        with ZipFile(BytesIO(data)) as archive:
            names = set(archive.namelist())
    except BadZipFile as exc:
        raise InvalidResumeError("The uploaded file is not a valid DOCX document.") from exc

    if not required_members.issubset(names):
        raise InvalidResumeError("The uploaded file is not a valid DOCX document.")


def validate_resume_upload(
    *,
    filename: str,
    content_type: str | None,
    data: bytes,
    max_size_bytes: int,
) -> ValidatedResumeUpload:
    safe_name = _safe_filename(filename)

    if not data:
        raise InvalidResumeError("The resume file is empty.")

    if len(data) > max_size_bytes:
        raise ResumeTooLargeError("The resume exceeds the maximum allowed size.")

    suffix = PurePosixPath(safe_name).suffix.lower()

    if suffix == ".pdf":
        extension: ResumeExtension = "pdf"
        canonical_content_type = "application/pdf"
        _validate_pdf(data)
    elif suffix == ".docx":
        extension = "docx"
        canonical_content_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        _validate_docx(data)
    else:
        raise InvalidResumeError("Only PDF and DOCX resumes are supported.")

    supplied_content_type = content_type.strip().lower() if content_type else ""

    allowed_supplied_types = {
        "",
        "application/octet-stream",
        canonical_content_type,
    }

    if supplied_content_type not in allowed_supplied_types:
        raise InvalidResumeError("The uploaded file type does not match its extension.")

    return ValidatedResumeUpload(
        original_filename=safe_name,
        extension=extension,
        content_type=canonical_content_type,
        data=data,
        sha256=sha256(data).hexdigest(),
    )


class ResumeService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        storage: ObjectStorage,
        max_size_bytes: int,
        repository: (ResumeRepository | None) = None,
    ) -> None:
        self._session = session
        self._storage = storage
        self._max_size_bytes = max_size_bytes
        self._repository = repository if repository is not None else ResumeRepository(session)

    @property
    def max_size_bytes(self) -> int:
        return self._max_size_bytes

    async def upload(
        self,
        *,
        user: User,
        filename: str,
        content_type: str | None,
        data: bytes,
    ) -> Resume:
        validated = validate_resume_upload(
            filename=filename,
            content_type=content_type,
            data=data,
            max_size_bytes=(self._max_size_bytes),
        )

        resume_id = uuid4()

        storage_key = f"resumes/{user.id}/{resume_id}/original.{validated.extension}"

        try:
            stored_file = await self._storage.save(
                key=storage_key,
                data=validated.data,
                content_type=(validated.content_type),
                checksum_sha256=(validated.sha256),
            )
        except StorageError as exc:
            raise (
                ResumeStorageUnavailableError("Resume storage is temporarily unavailable.")
            ) from exc

        resume = Resume(
            id=resume_id,
            user_id=user.id,
            original_filename=(validated.original_filename),
            storage_backend=(self._storage.name),
            storage_key=stored_file.key,
            storage_etag=stored_file.etag,
            content_type=(validated.content_type),
            file_extension=(validated.extension),
            file_size_bytes=(stored_file.size_bytes),
            sha256=validated.sha256,
        )

        self._repository.add(resume)

        try:
            await self._session.commit()
            await self._session.refresh(resume)
        except Exception as exc:
            await self._session.rollback()

            try:
                await self._storage.delete(key=stored_file.key)
            except StorageError:
                pass

            raise ResumePersistenceError("The resume metadata could not be saved.") from exc

        return resume
