"""Add leave carryover columns to leave_types and leave_balances.

Revision ID: 012
Revises: 011
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa

revision = "012_leave_carryover"
down_revision = "011_mt1_clinic_slug_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "leave_types",
        sa.Column("allow_carryover", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "leave_types",
        sa.Column("carryover_max_days", sa.Integer(), nullable=True),
    )
    op.add_column(
        "leave_balances",
        sa.Column(
            "carryover_days",
            sa.Numeric(6, 1),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("leave_balances", "carryover_days")
    op.drop_column("leave_types", "carryover_max_days")
    op.drop_column("leave_types", "allow_carryover")
