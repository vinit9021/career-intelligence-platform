"""Create application timeline events.

Revision ID: 20260815_0005
Revises: 20260813_0004
"""

from collections.abc import Sequence
from datetime import UTC, datetime, time
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "20260815_0005"

down_revision: str | None = "20260813_0004"

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "application_timeline_events",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "related_status",
            sa.String(length=32),
            nullable=True,
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            server_default="manual",
            nullable=False,
        ),
        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "event_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
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
            name=("ck_application_timeline_events_event_type_valid"),
        ),
        sa.CheckConstraint(
            ("source IN ('manual', 'system', 'gmail', 'integration')"),
            name=("ck_application_timeline_events_source_valid"),
        ),
        sa.CheckConstraint(
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
            name=("ck_application_timeline_events_related_status_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "source",
            "external_id",
            name=("uq_timeline_external_source"),
        ),
    )

    op.create_index(
        "ix_application_timeline_events_application_id",
        "application_timeline_events",
        ["application_id"],
        unique=False,
    )

    op.create_index(
        "ix_application_timeline_events_user_id",
        "application_timeline_events",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_application_timeline_events_event_type",
        "application_timeline_events",
        ["event_type"],
        unique=False,
    )

    op.create_index(
        "ix_timeline_application_event_at",
        "application_timeline_events",
        [
            "application_id",
            "event_at",
        ],
        unique=False,
    )

    # Backfill existing Day 23 applications so they
    # immediately receive an initial timeline event.
    connection = op.get_bind()

    applications = sa.table(
        "applications",
        sa.column(
            "id",
            sa.Uuid(),
        ),
        sa.column(
            "user_id",
            sa.Uuid(),
        ),
        sa.column(
            "applied_at",
            sa.Date(),
        ),
        sa.column(
            "status",
            sa.String(),
        ),
    )

    timeline = sa.table(
        "application_timeline_events",
        sa.column(
            "id",
            sa.Uuid(),
        ),
        sa.column(
            "application_id",
            sa.Uuid(),
        ),
        sa.column(
            "user_id",
            sa.Uuid(),
        ),
        sa.column(
            "event_type",
            sa.String(),
        ),
        sa.column(
            "title",
            sa.String(),
        ),
        sa.column(
            "description",
            sa.Text(),
        ),
        sa.column(
            "related_status",
            sa.String(),
        ),
        sa.column(
            "source",
            sa.String(),
        ),
        sa.column(
            "event_at",
            sa.DateTime(timezone=True),
        ),
    )

    rows = connection.execute(
        sa.select(
            applications.c.id,
            applications.c.user_id,
            applications.c.applied_at,
            applications.c.status,
        )
    ).mappings()

    for row in rows:
        event_at = datetime.combine(
            row["applied_at"],
            time.min,
            tzinfo=UTC,
        )

        connection.execute(
            timeline.insert().values(
                id=uuid4(),
                application_id=row["id"],
                user_id=row["user_id"],
                event_type=("application_submitted"),
                title=("Application submitted"),
                description=("Initial application event created during timeline setup."),
                related_status=row["status"],
                source="system",
                event_at=event_at,
            )
        )


def downgrade() -> None:
    op.drop_index(
        "ix_timeline_application_event_at",
        table_name=("application_timeline_events"),
    )

    op.drop_index(
        "ix_application_timeline_events_event_type",
        table_name=("application_timeline_events"),
    )

    op.drop_index(
        "ix_application_timeline_events_user_id",
        table_name=("application_timeline_events"),
    )

    op.drop_index(
        "ix_application_timeline_events_application_id",
        table_name=("application_timeline_events"),
    )

    op.drop_table("application_timeline_events")
