from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Application(Base):
    __tablename__ = "applications"

    __table_args__ = (
        CheckConstraint(
            (
                "status IN ("
                "'applied', "
                "'online_assessment', "
                "'interview', "
                "'offer', "
                "'rejected', "
                "'withdrawn'"
                ")"
            ),
            name="status_valid",
        ),
        CheckConstraint(
            ("source IN ('manual', 'gmail', 'integration')"),
            name="source_valid",
        ),
        UniqueConstraint(
            "user_id",
            "source",
            "external_id",
            name="uq_application_external_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
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

    company: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    job_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )

    applied_at: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="applied",
        server_default=text("'applied'"),
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="manual",
        server_default=text("'manual'"),
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    user: Mapped[User] = relationship(back_populates="applications")
