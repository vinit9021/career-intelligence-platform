"""Pydantic schemas for resume version management."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.resume_parsing import (
    ResumeStructuredContent,
)

ResumeVariant = Literal[
    "backend",
    "ai",
    "ml",
    "full_stack",
]


class ResumeVersionCreate(BaseModel):
    """Create a new resume variant version."""

    user_id: UUID
    variant: ResumeVariant
    content: ResumeStructuredContent
    source_resume_id: UUID | None = None

    ats_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    optimization_snapshot: dict[str, Any] | None = None

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    set_active: bool = True


class ResumeVersionRead(BaseModel):
    """Resume version returned by the manager."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    source_resume_id: UUID | None
    variant: ResumeVariant
    version_number: int
    content: dict[str, Any]
    optimization_snapshot: dict[str, Any] | None
    ats_score: float | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ResumeVersionActivate(BaseModel):
    """Activate a stored resume version."""

    user_id: UUID
    resume_version_id: UUID


class ResumeSubmissionCreate(BaseModel):
    """Track a submitted resume version."""

    user_id: UUID
    resume_version_id: UUID
    application_reference: str = Field(
        min_length=1,
        max_length=128,
    )
    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class ResumeSubmissionRead(BaseModel):
    """Stored resume submission."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_version_id: UUID
    application_reference: str
    notes: str | None
    submitted_at: datetime


class ResumeVersionHistory(BaseModel):
    """Version history for one resume variant."""

    user_id: UUID
    variant: ResumeVariant
    versions: list[ResumeVersionRead] = Field(default_factory=list)
