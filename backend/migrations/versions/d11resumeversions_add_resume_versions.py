"""Add resume version management tables.

Revision ID: d11resumeversions
Revises: 20260803_0003
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d11resumeversions"
down_revision: Union[str, None] = "20260803_0003"
branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None
depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    op.create_table(
        "resume_versions",
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
            "source_resume_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column(
            "variant",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "version_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "optimization_snapshot",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "ats_score",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["source_resume_id"],
            ["resumes.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "variant",
            "version_number",
            name="uq_resume_version_number",
        ),
    )

    op.create_index(
        "ix_resume_versions_user_id",
        "resume_versions",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_resume_versions_user_variant",
        "resume_versions",
        [
            "user_id",
            "variant",
        ],
        unique=False,
    )

    op.create_index(
        "uq_resume_versions_active_variant",
        "resume_versions",
        [
            "user_id",
            "variant",
        ],
        unique=True,
        postgresql_where=sa.text(
            "is_active = true"
        ),
    )

    op.create_table(
        "resume_version_submissions",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "resume_version_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "application_reference",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["resume_version_id"],
            ["resume_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "resume_version_id",
            "application_reference",
            name="uq_resume_version_submission",
        ),
    )

    op.create_index(
        "ix_resume_version_submissions_resume_version_id",
        "resume_version_submissions",
        ["resume_version_id"],
        unique=False,
    )

    op.create_index(
        "ix_resume_version_submissions_application",
        "resume_version_submissions",
        ["application_reference"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resume_version_submissions_application",
        table_name="resume_version_submissions",
    )

    op.drop_index(
        "ix_resume_version_submissions_resume_version_id",
        table_name="resume_version_submissions",
    )

    op.drop_table(
        "resume_version_submissions"
    )

    op.drop_index(
        "uq_resume_versions_active_variant",
        table_name="resume_versions",
    )

    op.drop_index(
        "ix_resume_versions_user_variant",
        table_name="resume_versions",
    )

    op.drop_index(
        "ix_resume_versions_user_id",
        table_name="resume_versions",
    )

    op.drop_table("resume_versions")
