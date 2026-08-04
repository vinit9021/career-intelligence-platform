from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.dependencies import CurrentUser
from app.api.dependencies.resume_library import ResumeLibraryServiceDependency
from app.core.private_files import build_private_file_headers
from app.schemas.auth import ErrorResponse
from app.schemas.resume_library import (
    ResumeDeleteResponse,
    ResumeDetailResponse,
    ResumeHistoryPage,
    ResumeParseStatusResponse,
    ResumeViewerResponse,
)
from app.services.resume_library import (
    ResumeDeletePersistenceError,
    ResumeDeleteStorageError,
    ResumeFileUnavailableError,
    ResumeLibraryNotFoundError,
)

router = APIRouter(prefix="/resume", tags=["resume-library"])


@router.get(
    "/history",
    response_model=ResumeHistoryPage,
)
async def list_resume_history(
    current_user: CurrentUser,
    service: ResumeLibraryServiceDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ResumeHistoryPage:
    return await service.list_history(
        user=current_user,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{resume_id}",
    response_model=ResumeDetailResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "The resume was not found for the current user.",
        }
    },
)
async def get_resume_detail(
    resume_id: UUID,
    current_user: CurrentUser,
    service: ResumeLibraryServiceDependency,
) -> ResumeDetailResponse:
    try:
        return await service.get_detail(user=current_user, resume_id=resume_id)
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{resume_id}/parse-status",
    response_model=ResumeParseStatusResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "The resume was not found for the current user.",
        }
    },
)
async def get_resume_parse_status(
    resume_id: UUID,
    current_user: CurrentUser,
    service: ResumeLibraryServiceDependency,
) -> ResumeParseStatusResponse:
    try:
        return await service.get_parse_status(
            user=current_user,
            resume_id=resume_id,
        )
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{resume_id}/viewer",
    response_model=ResumeViewerResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "The resume was not found for the current user.",
        }
    },
)
async def get_resume_viewer(
    resume_id: UUID,
    current_user: CurrentUser,
    service: ResumeLibraryServiceDependency,
) -> ResumeViewerResponse:
    try:
        return await service.get_viewer(user=current_user, resume_id=resume_id)
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{resume_id}/file",
    response_class=Response,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "The resume was not found for the current user.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "The stored resume is unavailable.",
        },
    },
)
async def download_resume_file(
    resume_id: UUID,
    current_user: CurrentUser,
    service: ResumeLibraryServiceDependency,
) -> Response:
    try:
        payload = await service.get_file(user=current_user, resume_id=resume_id)
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ResumeFileUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return Response(
        content=payload.data,
        media_type=payload.content_type,
        headers=build_private_file_headers(
            filename=payload.filename,
            sha256=payload.sha256,
            size_bytes=len(payload.data),
        ),
    )


@router.delete(
    "/{resume_id}",
    response_model=ResumeDeleteResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "The resume was not found for the current user.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "The stored resume could not be deleted.",
        },
    },
)
async def delete_resume(
    resume_id: UUID,
    current_user: CurrentUser,
    service: ResumeLibraryServiceDependency,
) -> ResumeDeleteResponse:
    try:
        return await service.delete_resume(user=current_user, resume_id=resume_id)
    except ResumeLibraryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ResumeDeleteStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ResumeDeletePersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
