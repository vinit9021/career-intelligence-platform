from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ApplicationTimelineEvent(Base):
    __tablename__ = "application_timeline_events"

    __table_args__ = (
        CheckConstraint(
            (
                "event_type IN ("
                "'application_submitted', "
                "'status_changed', "
                "'online_assessment_received', "
                "'online_assessment_completed', "
                "'interview_scheduled', "
                "'interview_completed', "
                "'offer_received', "
                "'rejected', "
                "'withdrawn', "
                "'note'"
                ")"
            ),
            name="event_type_valid",
        ),
        CheckConstraint(
            ("source IN ('manual', 'system', 'gmail', 'integration')"),
            name="source_valid",
        ),
        CheckConstraint(
            (
                "related_status IS NULL OR "
                "related_status IN ("
                "'applied', "
                "'online_assessment', "
                "'interview', "
                "'offer', "
                "'rejected', "
                "'withdrawn'"
                ")"
            ),
            name="related_status_valid",
        ),
        UniqueConstraint(
            "user_id",
            "source",
            "external_id",
            name="uq_timeline_external_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    application_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "applications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    related_status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
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

    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
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
