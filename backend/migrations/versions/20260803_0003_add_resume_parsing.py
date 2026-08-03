"""Add resume parsing state and structured results.

Revision ID: 20260803_0003
Revises: 20260803_0002
Create Date: 2026-08-03

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260803_0003"
down_revision: str | None = "20260803_0002"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    op.add_column(
        "resumes",
        sa.Column(
            "parse_status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
    )
    op.add_column(
        "resumes",
        sa.Column("parse_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        op.f("ck_resumes_parse_status_valid"),
        "resumes",
        "parse_status IN ('pending', 'processing', 'completed', 'needs_ocr', 'failed')",
    )

    op.create_table(
        "resume_parse_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(length=8), nullable=False),
        sa.Column("parser_name", sa.String(length=64), nullable=False),
        sa.Column("parser_version", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column(
            "structured_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "warnings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("character_count", sa.Integer(), nullable=False),
        sa.Column(
            "requires_ocr",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "source_type IN ('pdf', 'docx')",
            name=op.f("ck_resume_parse_results_source_type_valid"),
        ),
        sa.CheckConstraint(
            "character_count >= 0",
            name=op.f("ck_resume_parse_results_character_count_non_negative"),
        ),
        sa.CheckConstraint(
            "page_count IS NULL OR page_count > 0",
            name=op.f("ck_resume_parse_results_page_count_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["resume_id"],
            ["resumes.id"],
            name=op.f("fk_resume_parse_results_resume_id_resumes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resume_parse_results")),
    )
    op.create_index(
        op.f("ix_resume_parse_results_resume_id"),
        "resume_parse_results",
        ["resume_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_resume_parse_results_resume_id"),
        table_name="resume_parse_results",
    )
    op.drop_table("resume_parse_results")
    op.drop_constraint(
        op.f("ck_resumes_parse_status_valid"),
        "resumes",
        type_="check",
    )
    op.drop_column("resumes", "parsed_at")
    op.drop_column("resumes", "parse_error")
    op.drop_column("resumes", "parse_status")
