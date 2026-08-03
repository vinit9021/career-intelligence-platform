from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.resume_parse_result import ResumeParseResult
    from app.models.user import User


class Resume(Base):
    __tablename__ = "resumes"

    __table_args__ = (
        CheckConstraint("file_size_bytes > 0", name="positive_file_size"),
        CheckConstraint(
            "file_extension IN ('pdf', 'docx')",
            name="file_extension_valid",
        ),
        CheckConstraint(
            "storage_backend IN ('local', 's3')",
            name="storage_backend_valid",
        ),
        CheckConstraint(
            "parse_status IN ('pending', 'processing', 'completed', 'needs_ocr', 'failed')",
            name="parse_status_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_backend: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="local",
        server_default=text("'local'"),
    )
    storage_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        unique=True,
    )
    storage_etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str] = mapped_column(String(127), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(8), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parse_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="resumes")
    parse_result: Mapped[ResumeParseResult | None] = relationship(
        back_populates="resume",
        cascade="all, delete-orphan",
        passive_deletes=True,
        single_parent=True,
        uselist=False,
    )
