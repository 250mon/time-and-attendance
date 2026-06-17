"""create attendance_days

Revision ID: 004_create_attendance_days
Revises: 003_create_attendance_punches
Create Date: 2026-06-13 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_create_attendance_days"
down_revision: Union[str, None] = "003_create_attendance_punches"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

attendance_day_status_enum = postgresql.ENUM(
    "NOT_STARTED", "WORKING", "COMPLETED", "ABSENT", "HOLIDAY", "ON_LEAVE",
    name="attendance_day_status", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    attendance_day_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "attendance_days",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            attendance_day_status_enum,
            nullable=False,
            server_default="NOT_STARTED",
        ),
        sa.Column("scheduled_minutes", sa.Integer(), nullable=True),
        sa.Column("actual_clock_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_clock_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("worked_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("regular_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overtime_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("late_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("early_leave_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "work_date", name="uq_attendance_days_user_date"),
    )
    op.create_index(
        op.f("ix_attendance_days_clinic_id"), "attendance_days", ["clinic_id"], unique=False
    )
    op.create_index(
        op.f("ix_attendance_days_user_id"), "attendance_days", ["user_id"], unique=False
    )
    op.create_index(
        "ix_attendance_days_user_work_date",
        "attendance_days",
        ["user_id", "work_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_attendance_days_user_work_date", table_name="attendance_days")
    op.drop_index(op.f("ix_attendance_days_user_id"), table_name="attendance_days")
    op.drop_index(op.f("ix_attendance_days_clinic_id"), table_name="attendance_days")
    op.drop_table("attendance_days")

    bind = op.get_bind()
    attendance_day_status_enum.drop(bind, checkfirst=True)
