import uuid as _uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    __table_args__ = (UniqueConstraint("user_id", "leave_type_id", "year"),)

    id: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    clinic_id: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    user_id: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    leave_type_id: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leave_types.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_days: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False, default=Decimal("0"))
    used_days: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    adjustments: Mapped[list["LeaveBalanceAdjustment"]] = relationship(
        "LeaveBalanceAdjustment", back_populates="balance"
    )


class LeaveBalanceAdjustment(Base):
    __tablename__ = "leave_balance_adjustments"

    id: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)
    clinic_id: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False)
    leave_balance_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leave_balances.id"), nullable=False, index=True
    )
    adjusted_by: Mapped[_uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    delta_days: Mapped[Decimal] = mapped_column(Numeric(6, 1), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    balance: Mapped["LeaveBalance"] = relationship("LeaveBalance", back_populates="adjustments")
