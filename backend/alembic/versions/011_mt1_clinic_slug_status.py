"""mt1 clinic slug and status

Revision ID: 011_mt1_clinic_slug_status
Revises: 010_mt1_email_unique_per_clinic
Create Date: 2026-06-27 01:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_mt1_clinic_slug_status"
down_revision: Union[str, None] = "010_mt1_email_unique_per_clinic"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

clinic_status_enum = postgresql.ENUM(
    "ACTIVE",
    "SUSPENDED",
    name="clinic_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    clinic_status_enum.create(bind, checkfirst=True)

    op.add_column("clinics", sa.Column("slug", sa.String(64), nullable=True))
    op.add_column("clinics", sa.Column("status", clinic_status_enum, nullable=True))

    # Backfill slug from clinic name: lowercase, collapse non-alphanumeric to hyphens,
    # strip leading/trailing hyphens, and truncate to 64 chars.
    op.execute(
        """
        UPDATE clinics
        SET slug = LEFT(
            TRIM(BOTH '-' FROM
                REGEXP_REPLACE(LOWER(TRIM(name)), '[^a-z0-9]+', '-', 'g')
            ),
            64
        )
        WHERE slug IS NULL
        """
    )

    op.execute("UPDATE clinics SET status = 'ACTIVE' WHERE status IS NULL")

    op.alter_column("clinics", "slug", nullable=False)
    op.alter_column("clinics", "status", nullable=False)

    op.create_unique_constraint("uq_clinics_slug", "clinics", ["slug"])
    op.create_index(op.f("ix_clinics_slug"), "clinics", ["slug"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_clinics_slug"), table_name="clinics")
    op.drop_constraint("uq_clinics_slug", "clinics", type_="unique")
    op.drop_column("clinics", "status")
    op.drop_column("clinics", "slug")

    bind = op.get_bind()
    clinic_status_enum.drop(bind, checkfirst=True)
