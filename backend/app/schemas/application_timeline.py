from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.application import ApplicationStatus

TimelineEventType = Literal[
    "application_submitted",
    "status_changed",
    "online_assessment_received",
    "online_assessment_completed",
    "interview_scheduled",
    "interview_completed",
    "offer_received",
    "rejected",
    "withdrawn",
    "note",
]

TimelineEventSource = Literal[
    "manual",
    "system",
    "gmail",
    "integration",
]

TimelineSortOrder = Literal[
    "asc",
    "desc",
]


class ApplicationTimelineCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_type: TimelineEventType = "note"

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    related_status: ApplicationStatus | None = None

    event_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ApplicationTimelineUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    event_type: TimelineEventType | None = None

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    related_status: ApplicationStatus | None = None

    event_at: datetime | None = None


class ApplicationTimelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    event_type: TimelineEventType
    title: str
    description: str | None
    related_status: ApplicationStatus | None
    source: TimelineEventSource
    external_id: str | None
    event_at: datetime
    created_at: datetime
    updated_at: datetime
