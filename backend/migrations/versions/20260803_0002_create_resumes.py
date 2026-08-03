"""Create resumes table.

Revision ID: 20260803_0002
Revises: 20260803_0001
Create Date: 2026-08-03

"""

import sqlalchemy as sa
from alembic import op

revision: str = "20260803_0002"
down_revision: str | None = "20260803_0001"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "resumes",
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
            "original_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "storage_backend",
            sa.String(length=16),
            server_default=sa.text("'local'"),
            nullable=False,
        ),
        sa.Column(
            "storage_key",
            sa.String(length=512),
            nullable=False,
        ),
        sa.Column(
            "storage_etag",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "content_type",
            sa.String(length=127),
            nullable=False,
        ),
        sa.Column(
            "file_extension",
            sa.String(length=8),
            nullable=False,
        ),
        sa.Column(
            "file_size_bytes",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "sha256",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "file_size_bytes > 0",
            name=op.f("ck_resumes_positive_file_size"),
        ),
        sa.CheckConstraint(
            ("file_extension IN ('pdf', 'docx')"),
            name=op.f("ck_resumes_file_extension_valid"),
        ),
        sa.CheckConstraint(
            ("storage_backend IN ('local', 's3')"),
            name=op.f("ck_resumes_storage_backend_valid"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_resumes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_resumes"),
        ),
        sa.UniqueConstraint(
            "storage_key",
            name=op.f("uq_resumes_storage_key"),
        ),
    )

    op.create_index(
        op.f("ix_resumes_user_id"),
        "resumes",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_resumes_sha256"),
        "resumes",
        ["sha256"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_resumes_sha256"),
        table_name="resumes",
    )

    op.drop_index(
        op.f("ix_resumes_user_id"),
        table_name="resumes",
    )

    op.drop_table("resumes")
