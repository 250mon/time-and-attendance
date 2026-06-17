"""create leave_types and leave_requests

Revision ID: 006_create_leave_tables
Revises: 005_correction_requests
Create Date: 2026-06-13 14:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_create_leave_tables"
down_revision: Union[str, None] = "005_correction_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

leave_status_enum = postgresql.ENUM(
    "PENDING", "APPROVED", "REJECTED", "CANCELLED",
    name="leave_status", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    leave_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "leave_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("default_days_per_year", sa.Integer(), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_leave_types_clinic_id"), "leave_types", ["clinic_id"], unique=False
    )

    op.create_table(
        "leave_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("leave_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("total_days", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", leave_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["leave_type_id"], ["leave_types.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_leave_requests_clinic_id"), "leave_requests", ["clinic_id"], unique=False
    )
    op.create_index(
        op.f("ix_leave_requests_user_id"), "leave_requests", ["user_id"], unique=False
    )
    op.create_index(
        "ix_leave_requests_user_dates",
        "leave_requests",
        ["user_id", "start_date", "end_date"],
        unique=False,
    )
    op.create_index(
        "ix_leave_requests_status",
        "leave_requests",
        ["clinic_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_leave_requests_status", table_name="leave_requests")
    op.drop_index("ix_leave_requests_user_dates", table_name="leave_requests")
    op.drop_index(op.f("ix_leave_requests_user_id"), table_name="leave_requests")
    op.drop_index(op.f("ix_leave_requests_clinic_id"), table_name="leave_requests")
    op.drop_table("leave_requests")
    op.drop_index(op.f("ix_leave_types_clinic_id"), table_name="leave_types")
    op.drop_table("leave_types")

    bind = op.get_bind()
    leave_status_enum.drop(bind, checkfirst=True)
