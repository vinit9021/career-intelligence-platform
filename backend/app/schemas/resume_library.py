from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.resume_parsing import ResumeParseMetadata, ResumeStructuredContent

ResumeLifecycleStatus = Literal[
    "pending",
    "processing",
    "completed",
    "needs_ocr",
    "failed",
]
ResumeStorageBackend = Literal["local", "s3"]
ResumeFileExtension = Literal["pdf", "docx"]


class ResumeHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    content_type: str
    file_extension: ResumeFileExtension
    file_size_bytes: int = Field(gt=0)
    storage_backend: ResumeStorageBackend
    parse_status: ResumeLifecycleStatus
    parsed_at: datetime | None
    created_at: datetime


class ResumeHistoryPage(BaseModel):
    items: list[ResumeHistoryItem]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class ResumeDetailResponse(ResumeHistoryItem):
    sha256: str = Field(min_length=64, max_length=64)
    parse_error: str | None


class ResumeParseStatusResponse(BaseModel):
    resume_id: UUID
    status: ResumeLifecycleStatus
    error: str | None
    parsed_at: datetime | None
    has_parsed_result: bool


class ResumeViewerResponse(BaseModel):
    resume: ResumeDetailResponse
    content: ResumeStructuredContent | None
    raw_text: str | None
    metadata: ResumeParseMetadata | None


class ResumeDeleteResponse(BaseModel):
    resume_id: UUID
    deleted: Literal[True] = True
    message: str = "Resume deleted successfully."
