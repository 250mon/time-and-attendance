import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AttendanceDayStatus


class AttendanceDay(Base):
    __tablename__ = "attendance_days"
    __table_args__ = (
        UniqueConstraint("user_id", "work_date", name="uq_attendance_days_user_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    work_date: Mapped[date] = mapped_column(Date(), nullable=False)
    status: Mapped[AttendanceDayStatus] = mapped_column(
        Enum(AttendanceDayStatus, name="attendance_day_status"),
        nullable=False,
        default=AttendanceDayStatus.NOT_STARTED,
    )
    scheduled_minutes: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    actual_clock_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    worked_minutes: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    regular_minutes: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    overtime_minutes: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    late_minutes: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    early_leave_minutes: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    break_minutes: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    is_locked: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
