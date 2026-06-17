"""add tenure_based to leave_types

Revision ID: 009_leave_type_tenure_based
Revises: 008_closings_and_audit
Create Date: 2026-06-13 18:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_leave_type_tenure_based"
down_revision: Union[str, None] = "008_closings_and_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leave_types",
        sa.Column(
            "tenure_based",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("leave_types", "tenure_based")
