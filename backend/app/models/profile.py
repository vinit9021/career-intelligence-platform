from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


PROFILE_LIST_TYPE = JSON().with_variant(
    JSONB(),
    "postgresql",
)


class Profile(Base):
    __tablename__ = "profiles"

    __table_args__ = (
        CheckConstraint(
            ("years_experience IS NULL OR (years_experience >= 0 AND years_experience <= 80)"),
            name="years_experience_range",
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
        unique=True,
        index=True,
    )
    headline: Mapped[str | None] = mapped_column(
        String(160),
        nullable=True,
    )
    location: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    years_experience: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    target_roles: Mapped[list[str]] = mapped_column(
        PROFILE_LIST_TYPE,
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    skills: Mapped[list[str]] = mapped_column(
        PROFILE_LIST_TYPE,
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    linkedin_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    github_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    portfolio_url: Mapped[str | None] = mapped_column(
        String(500),
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

    user: Mapped[User] = relationship(
        back_populates="profile",
    )
