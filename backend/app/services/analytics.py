from datetime import date

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models import User
from app.repositories.analytics import (
    AnalyticsRepository,
)
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    AnalyticsSummary,
    ApplicationTrendPoint,
    RecentActivityItem,
    StatusBreakdownItem,
)
from app.schemas.application import (
    ApplicationStatus,
)

STATUS_ORDER: tuple[
    ApplicationStatus,
    ...,
] = (
    "applied",
    "online_assessment",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
)


STATUS_LABELS: dict[
    ApplicationStatus,
    str,
] = {
    "applied": "Applied",
    "online_assessment": ("Online Assessment"),
    "interview": "Interview",
    "offer": "Offer",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
}


def _percentage(
    count: int,
    total: int,
) -> float:
    if total == 0:
        return 0.0

    return round(
        count / total * 100,
        1,
    )


def _month_start(
    value: date,
) -> date:
    return date(
        value.year,
        value.month,
        1,
    )


def _shift_month(
    value: date,
    months: int,
) -> date:
    month_index = value.year * 12 + value.month - 1 + months

    year = month_index // 12

    month = month_index % 12 + 1

    return date(
        year,
        month,
        1,
    )


class AnalyticsService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        repository: (AnalyticsRepository | None) = None,
    ) -> None:
        self._repository = repository if repository is not None else AnalyticsRepository(session)

    async def get_overview(
        self,
        *,
        user: User,
    ) -> AnalyticsOverviewResponse:
        counts = await self._repository.get_status_counts(user_id=user.id)

        total = sum(counts.values())

        applied = counts.get(
            "applied",
            0,
        )

        assessments = counts.get(
            "online_assessment",
            0,
        )

        interviews = counts.get(
            "interview",
            0,
        )

        offers = counts.get(
            "offer",
            0,
        )

        rejections = counts.get(
            "rejected",
            0,
        )

        active = applied + assessments + interviews

        summary = AnalyticsSummary(
            total_applications=total,
            active_applications=active,
            online_assessments=(assessments),
            interviews=interviews,
            offers=offers,
            rejections=rejections,
            active_rate=_percentage(
                active,
                total,
            ),
            interview_rate=_percentage(
                interviews,
                total,
            ),
            offer_rate=_percentage(
                offers,
                total,
            ),
            rejection_rate=_percentage(
                rejections,
                total,
            ),
        )

        status_breakdown = [
            StatusBreakdownItem(
                status=status_name,
                count=counts.get(
                    status_name,
                    0,
                ),
                percentage=_percentage(
                    counts.get(
                        status_name,
                        0,
                    ),
                    total,
                ),
            )
            for status_name in STATUS_ORDER
        ]

        application_dates = await self._repository.get_application_dates(user_id=user.id)

        application_trend = self._build_trend(application_dates)

        activity_records = await self._repository.get_recent_activity(
            user_id=user.id,
            limit=8,
        )

        recent_activity = [
            RecentActivityItem(
                event_id=(record.event_id),
                application_id=(record.application_id),
                company=record.company,
                role=record.role,
                event_type=(record.event_type),
                title=record.title,
                source=record.source,
                event_at=record.event_at,
            )
            for record in activity_records
        ]

        return AnalyticsOverviewResponse(
            summary=summary,
            status_breakdown=(status_breakdown),
            application_trend=(application_trend),
            recent_activity=(recent_activity),
        )

    def _build_trend(
        self,
        application_dates: list[date],
    ) -> list[ApplicationTrendPoint]:
        current_month = _month_start(date.today())

        months = [
            _shift_month(
                current_month,
                offset,
            )
            for offset in range(
                -5,
                1,
            )
        ]

        counts: dict[
            date,
            int,
        ] = {month: 0 for month in months}

        for applied_at in application_dates:
            key = _month_start(applied_at)

            if key in counts:
                counts[key] += 1

        return [
            ApplicationTrendPoint(
                period=(month.strftime("%Y-%m")),
                label=(month.strftime("%b %Y")),
                count=counts[month],
            )
            for month in months
        ]
