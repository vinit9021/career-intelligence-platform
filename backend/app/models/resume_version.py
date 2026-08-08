"""Database models for resume version management."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResumeVersion(Base):
    """Persisted resume variant/version."""

    __tablename__ = "resume_versions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "variant",
            "version_number",
            name="uq_resume_version_number",
        ),
        Index(
            "ix_resume_versions_user_variant",
            "user_id",
            "variant",
        ),
        Index(
            "uq_resume_versions_active_variant",
            "user_id",
            "variant",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    source_resume_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "resumes.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    variant: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    optimization_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    ats_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class ResumeVersionSubmission(Base):
    """Tracks which resume version was submitted."""

    __tablename__ = "resume_version_submissions"

    __table_args__ = (
        UniqueConstraint(
            "resume_version_id",
            "application_reference",
            name="uq_resume_version_submission",
        ),
        Index(
            "ix_resume_version_submissions_application",
            "application_reference",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    resume_version_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "resume_versions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    application_reference: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
