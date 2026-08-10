"""Models used by agent memory management."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

MemoryScope = Literal[
    "short_term",
    "long_term",
]

MemoryNamespace = Literal[
    "user_preferences",
    "career_goals",
    "resume_context",
    "application_context",
    "agent_insights",
    "workflow",
]


class MemoryRecord(BaseModel):
    """One stored memory item."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))

    user_id: str = Field(min_length=1)

    scope: MemoryScope

    namespace: MemoryNamespace

    key: str = Field(
        min_length=1,
        pattern=(r"^[a-zA-Z0-9_.:-]+$"),
    )

    value: Any

    session_id: str | None = None

    source_agent: str | None = None

    metadata: dict[str, str] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
