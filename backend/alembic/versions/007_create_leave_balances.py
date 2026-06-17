"""create leave_balances and leave_balance_adjustments

Revision ID: 007_create_leave_balances
Revises: 006_create_leave_tables
Create Date: 2026-06-13 15:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_create_leave_balances"
down_revision: Union[str, None] = "006_create_leave_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leave_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("leave_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("balance_days", sa.Numeric(6, 1), nullable=False, server_default="0"),
        sa.Column("used_days", sa.Numeric(6, 1), nullable=False, server_default="0"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "leave_type_id", "year", name="uq_leave_balances_user_type_year"),
    )
    op.create_index(op.f("ix_leave_balances_user_id"), "leave_balances", ["user_id"], unique=False)
    op.create_index(op.f("ix_leave_balances_leave_type_id"), "leave_balances", ["leave_type_id"], unique=False)
    op.create_index(op.f("ix_leave_balances_clinic_id"), "leave_balances", ["clinic_id"], unique=False)

    op.create_table(
        "leave_balance_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("leave_balance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("adjusted_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("delta_days", sa.Numeric(6, 1), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"]),
        sa.ForeignKeyConstraint(["leave_balance_id"], ["leave_balances.id"]),
        sa.ForeignKeyConstraint(["adjusted_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_leave_balance_adjustments_leave_balance_id"),
        "leave_balance_adjustments",
        ["leave_balance_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_leave_balance_adjustments_leave_balance_id"),
        table_name="leave_balance_adjustments",
    )
    op.drop_table("leave_balance_adjustments")

    op.drop_index(op.f("ix_leave_balances_clinic_id"), table_name="leave_balances")
    op.drop_index(op.f("ix_leave_balances_leave_type_id"), table_name="leave_balances")
    op.drop_index(op.f("ix_leave_balances_user_id"), table_name="leave_balances")
    op.drop_table("leave_balances")
