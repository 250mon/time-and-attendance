"""create shifts and staff_schedules

Revision ID: 002_create_shifts_schedules
Revises: 001_create_clinics_users
Create Date: 2026-06-12 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_create_shifts_schedules"
down_revision: Union[str, None] = "001_create_clinics_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schedule_status_enum = postgresql.ENUM(
    "SCHEDULED",
    "OFF",
    "HOLIDAY",
    "CANCELLED",
    name="schedule_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    schedule_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "shifts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("crosses_midnight", sa.Boolean(), nullable=False, server_default="false"),
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
    op.create_index(op.f("ix_shifts_clinic_id"), "shifts", ["clinic_id"], unique=False)

    op.create_table(
        "staff_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("scheduled_start", sa.Time(), nullable=True),
        sa.Column("scheduled_end", sa.Time(), nullable=True),
        sa.Column(
            "scheduled_break_minutes", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "status", schedule_status_enum, nullable=False, server_default="SCHEDULED"
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
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "work_date", name="uq_staff_schedules_user_date"),
    )
    op.create_index(
        op.f("ix_staff_schedules_clinic_id"), "staff_schedules", ["clinic_id"], unique=False
    )
    op.create_index(
        op.f("ix_staff_schedules_user_id"), "staff_schedules", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_staff_schedules_user_id"), table_name="staff_schedules")
    op.drop_index(op.f("ix_staff_schedules_clinic_id"), table_name="staff_schedules")
    op.drop_table("staff_schedules")
    op.drop_index(op.f("ix_shifts_clinic_id"), table_name="shifts")
    op.drop_table("shifts")

    bind = op.get_bind()
    schedule_status_enum.drop(bind, checkfirst=True)
