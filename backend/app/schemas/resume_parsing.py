from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ResumeParseStatus = Literal["completed", "needs_ocr"]
ResumeSourceType = Literal["pdf", "docx"]


class ResumeContactInformation(BaseModel):
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None


class ResumeStructuredContent(BaseModel):
    contact: ResumeContactInformation = Field(default_factory=ResumeContactInformation)
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class ResumeParseMetadata(BaseModel):
    source_type: ResumeSourceType
    parser_name: str
    parser_version: str
    page_count: int | None
    character_count: int = Field(ge=0)
    requires_ocr: bool
    warnings: list[str] = Field(default_factory=list)


class ResumeParseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    status: ResumeParseStatus
    content: ResumeStructuredContent
    raw_text: str
    metadata: ResumeParseMetadata
    parsed_at: datetime
