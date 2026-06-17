"""create attendance_correction_requests

Revision ID: 005_create_attendance_corrections
Revises: 004_create_attendance_days
Create Date: 2026-06-13 13:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_correction_requests"
down_revision: Union[str, None] = "004_create_attendance_days"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

correction_status_enum = postgresql.ENUM(
    "PENDING", "APPROVED", "REJECTED", "CANCELLED",
    name="correction_status", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    correction_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "attendance_correction_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            correction_status_enum,
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("corrected_clock_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("corrected_clock_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_attendance_correction_requests_clinic_id"),
        "attendance_correction_requests",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_correction_requests_user_id"),
        "attendance_correction_requests",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_attendance_correction_requests_user_work_date",
        "attendance_correction_requests",
        ["user_id", "work_date"],
        unique=False,
    )
    op.create_index(
        "ix_attendance_correction_requests_status",
        "attendance_correction_requests",
        ["clinic_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_attendance_correction_requests_status", table_name="attendance_correction_requests")
    op.drop_index("ix_attendance_correction_requests_user_work_date", table_name="attendance_correction_requests")
    op.drop_index(op.f("ix_attendance_correction_requests_user_id"), table_name="attendance_correction_requests")
    op.drop_index(op.f("ix_attendance_correction_requests_clinic_id"), table_name="attendance_correction_requests")
    op.drop_table("attendance_correction_requests")

    bind = op.get_bind()
    correction_status_enum.drop(bind, checkfirst=True)
