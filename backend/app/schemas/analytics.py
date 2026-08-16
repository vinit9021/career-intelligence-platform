from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.application import (
    ApplicationStatus,
)
from app.schemas.application_timeline import (
    TimelineEventSource,
    TimelineEventType,
)


class AnalyticsSummary(BaseModel):
    total_applications: int
    active_applications: int
    online_assessments: int
    interviews: int
    offers: int
    rejections: int

    active_rate: float
    interview_rate: float
    offer_rate: float
    rejection_rate: float


class StatusBreakdownItem(BaseModel):
    status: ApplicationStatus
    count: int
    percentage: float


class ApplicationTrendPoint(BaseModel):
    period: str
    label: str
    count: int


class RecentActivityItem(BaseModel):
    event_id: UUID
    application_id: UUID

    company: str
    role: str

    event_type: TimelineEventType
    title: str
    source: TimelineEventSource

    event_at: datetime


class AnalyticsOverviewResponse(BaseModel):
    summary: AnalyticsSummary

    status_breakdown: list[StatusBreakdownItem]

    application_trend: list[ApplicationTrendPoint]

    recent_activity: list[RecentActivityItem]
