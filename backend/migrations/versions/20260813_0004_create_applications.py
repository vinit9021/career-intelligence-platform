"""Create applications table.

Revision ID: 20260813_0004
Revises: d11resumeversions
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260813_0004"

down_revision: str | None = "d11resumeversions"

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "company",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "job_url",
            sa.String(length=2048),
            nullable=True,
        ),
        sa.Column(
            "location",
            sa.String(length=160),
            nullable=True,
        ),
        sa.Column(
            "applied_at",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=("applied"),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            server_default=("manual"),
            nullable=False,
        ),
        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=(sa.text("now()")),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=(sa.text("now()")),
            nullable=False,
        ),
        sa.CheckConstraint(
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
            name=("ck_applications_status_valid"),
        ),
        sa.CheckConstraint(
            ("source IN ('manual', 'gmail', 'integration')"),
            name=("ck_applications_source_valid"),
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
            name=("uq_application_external_source"),
        ),
    )

    op.create_index(
        "ix_applications_user_id",
        "applications",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_applications_status",
        "applications",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_applications_user_status",
        "applications",
        [
            "user_id",
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_applications_user_applied_at",
        "applications",
        [
            "user_id",
            "applied_at",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_applications_user_applied_at",
        table_name="applications",
    )

    op.drop_index(
        "ix_applications_user_status",
        table_name="applications",
    )

    op.drop_index(
        "ix_applications_status",
        table_name="applications",
    )

    op.drop_index(
        "ix_applications_user_id",
        table_name="applications",
    )

    op.drop_table("applications")
