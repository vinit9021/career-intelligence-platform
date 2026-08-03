from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.dependencies import (
    CurrentUser,
    ResumeParsingServiceDependency,
    ResumeServiceDependency,
)
from app.schemas.auth import ErrorResponse
from app.schemas.resume_parsing import ResumeParseResponse
from app.schemas.resumes import ResumeResponse
from app.services.resume_parsing import (
    ResumeNotFoundError,
    ResumeParseResultNotFoundError,
    ResumeParsingFailedError,
    ResumeParsingPersistenceError,
    ResumeSourceUnavailableError,
)
from app.services.resumes import (
    InvalidResumeError,
    ResumePersistenceError,
    ResumeStorageUnavailableError,
    ResumeTooLargeError,
)

router = APIRouter(prefix="/resume", tags=["resumes"])


@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_413_CONTENT_TOO_LARGE: {
            "model": ErrorResponse,
            "description": "The resume exceeds the configured upload limit.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "The uploaded resume is invalid.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "The configured storage backend is unavailable.",
        },
    },
)
async def upload_resume(
    file: Annotated[
        UploadFile,
        File(description="Resume file in PDF or DOCX format."),
    ],
    current_user: CurrentUser,
    service: ResumeServiceDependency,
) -> ResumeResponse:
    try:
        data = await file.read(service.max_size_bytes + 1)
    finally:
        await file.close()

    try:
        resume = await service.upload(
            user=current_user,
            filename=file.filename or "",
            content_type=file.content_type,
            data=data,
        )
    except ResumeTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except InvalidResumeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ResumeStorageUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ResumePersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The resume metadata could not be saved.",
        ) from exc

    return ResumeResponse.model_validate(resume)


@router.post(
    "/{resume_id}/parse",
    response_model=ResumeParseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "The resume does not exist for the current user.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "The resume could not be parsed.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "The stored resume is unavailable.",
        },
    },
)
async def parse_resume(
    resume_id: UUID,
    current_user: CurrentUser,
    service: ResumeParsingServiceDependency,
) -> ResumeParseResponse:
    try:
        return await service.parse_resume(user=current_user, resume_id=resume_id)
    except ResumeNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ResumeParsingFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except ResumeSourceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ResumeParsingPersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The parsed resume could not be persisted.",
        ) from exc


@router.get(
    "/{resume_id}/parsed",
    response_model=ResumeParseResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "The resume or parsed result was not found.",
        }
    },
)
async def get_parsed_resume(
    resume_id: UUID,
    current_user: CurrentUser,
    service: ResumeParsingServiceDependency,
) -> ResumeParseResponse:
    try:
        return await service.get_parse_result(
            user=current_user,
            resume_id=resume_id,
        )
    except (ResumeNotFoundError, ResumeParseResultNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
