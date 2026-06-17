import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Time, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ScheduleStatus


class StaffSchedule(Base):
    __tablename__ = "staff_schedules"
    __table_args__ = (
        UniqueConstraint("user_id", "work_date", name="uq_staff_schedules_user_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    shift_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shifts.id"), nullable=True
    )
    work_date: Mapped[date] = mapped_column(Date(), nullable=False)
    scheduled_start: Mapped[time | None] = mapped_column(Time(), nullable=True)
    scheduled_end: Mapped[time | None] = mapped_column(Time(), nullable=True)
    scheduled_break_minutes: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    status: Mapped[ScheduleStatus] = mapped_column(
        Enum(ScheduleStatus, name="schedule_status"), nullable=False, default=ScheduleStatus.SCHEDULED
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
