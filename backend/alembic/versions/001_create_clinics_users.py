"""create clinics and users

Revision ID: 001_create_clinics_users
Revises:
Create Date: 2026-06-12 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_create_clinics_users"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role_enum = postgresql.ENUM(
    "OWNER",
    "ADMIN",
    "MANAGER",
    "STAFF",
    name="user_role",
    create_type=False,
)
employment_type_enum = postgresql.ENUM(
    "FULL_TIME",
    "PART_TIME",
    "CONTRACT",
    "TEMPORARY",
    name="employment_type",
    create_type=False,
)
user_status_enum = postgresql.ENUM(
    "ACTIVE",
    "INACTIVE",
    "TERMINATED",
    name="user_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    employment_type_enum.create(bind, checkfirst=True)
    user_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("ip_whitelist", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("employment_type", employment_type_enum, nullable=False),
        sa.Column("hire_date", sa.Date(), nullable=True),
        sa.Column("termination_date", sa.Date(), nullable=True),
        sa.Column("status", user_status_enum, nullable=False),
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
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_clinic_id"), "users", ["clinic_id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_clinic_id"), table_name="users")
    op.drop_table("users")
    op.drop_table("clinics")

    bind = op.get_bind()
    user_status_enum.drop(bind, checkfirst=True)
    employment_type_enum.drop(bind, checkfirst=True)
    user_role_enum.drop(bind, checkfirst=True)
