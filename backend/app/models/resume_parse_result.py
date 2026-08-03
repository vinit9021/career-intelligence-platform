from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.resume import Resume

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class ResumeParseResult(Base):
    __tablename__ = "resume_parse_results"

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('pdf', 'docx')",
            name="source_type_valid",
        ),
        CheckConstraint(
            "character_count >= 0",
            name="character_count_non_negative",
        ),
        CheckConstraint(
            "page_count IS NULL OR page_count > 0",
            name="page_count_positive",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    resume_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(8), nullable=False)
    parser_name: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_data: Mapped[dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
    )
    warnings: Mapped[list[str]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=list,
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    character_count: Mapped[int] = mapped_column(Integer, nullable=False)
    requires_ocr: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    resume: Mapped[Resume] = relationship(back_populates="parse_result")
