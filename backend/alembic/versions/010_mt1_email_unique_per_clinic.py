"""mt1 per-clinic email uniqueness

Revision ID: 010_mt1_email_unique_per_clinic
Revises: 009_leave_type_tenure_based
Create Date: 2026-06-27 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "010_mt1_email_unique_per_clinic"
down_revision: Union[str, None] = "009_leave_type_tenure_based"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Pre-flight: fail loudly if data already violates the new constraint.
    # This is a no-op on clean single-clinic deployments (no duplicates possible).
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT clinic_id, email
                FROM users
                GROUP BY clinic_id, email
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION
                    'Duplicate (clinic_id, email) pairs found; '
                    'resolve data before applying migration 010';
            END IF;
        END
        $$;
        """
    )
    op.drop_constraint("users_email_key", "users", type_="unique")
    op.create_unique_constraint("uq_users_clinic_email", "users", ["clinic_id", "email"])


def downgrade() -> None:
    op.drop_constraint("uq_users_clinic_email", "users", type_="unique")
    op.create_unique_constraint("users_email_key", "users", ["email"])
