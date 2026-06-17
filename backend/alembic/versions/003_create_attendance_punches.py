"""create attendance_punches

Revision ID: 003_create_attendance_punches
Revises: 002_create_shifts_schedules
Create Date: 2026-06-12 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_create_attendance_punches"
down_revision: Union[str, None] = "002_create_shifts_schedules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

punch_type_enum = postgresql.ENUM(
    "CLOCK_IN", "CLOCK_OUT", "BREAK_START", "BREAK_END", "MANUAL",
    name="punch_type", create_type=False,
)
punch_source_enum = postgresql.ENUM(
    "WEB", "MOBILE_WEB", "ADMIN", "QR", "GPS", "BIOMETRIC",
    name="punch_source", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    punch_type_enum.create(bind, checkfirst=True)
    punch_source_enum.create(bind, checkfirst=True)

    op.create_table(
        "attendance_punches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("punch_type", punch_type_enum, nullable=False),
        sa.Column("punched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", punch_source_enum, nullable=False, server_default="WEB"),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("device_info", sa.Text(), nullable=True),
        sa.Column("geo_lat", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("geo_lng", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("qr_code_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_attendance_punches_clinic_id"), "attendance_punches", ["clinic_id"], unique=False
    )
    op.create_index(
        op.f("ix_attendance_punches_user_id"), "attendance_punches", ["user_id"], unique=False
    )
    op.create_index(
        "ix_attendance_punches_user_punched_at",
        "attendance_punches",
        ["user_id", "punched_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_attendance_punches_user_punched_at", table_name="attendance_punches")
    op.drop_index(op.f("ix_attendance_punches_user_id"), table_name="attendance_punches")
    op.drop_index(op.f("ix_attendance_punches_clinic_id"), table_name="attendance_punches")
    op.drop_table("attendance_punches")

    bind = op.get_bind()
    punch_source_enum.drop(bind, checkfirst=True)
    punch_type_enum.drop(bind, checkfirst=True)
