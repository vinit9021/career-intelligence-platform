from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

NotificationType = Literal[
    "application_update",
    "online_assessment",
    "interview",
    "offer",
    "rejection",
    "general",
]

NotificationSource = Literal[
    "system",
    "gmail",
    "integration",
]


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID | None

    type: NotificationType
    title: str
    message: str

    is_read: bool
    source: NotificationSource

    read_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationPageResponse(BaseModel):
    items: list[NotificationResponse]

    total: int
    page: int
    page_size: int


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int
