import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import CorrectionStatus


class AttendanceCorrectionRequest(Base):
    __tablename__ = "attendance_correction_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    work_date: Mapped[date] = mapped_column(Date(), nullable=False)
    status: Mapped[CorrectionStatus] = mapped_column(
        Enum(CorrectionStatus, name="correction_status"),
        nullable=False,
        default=CorrectionStatus.PENDING,
    )
    # Corrected times stored as UTC datetimes; None means "no correction for this field"
    corrected_clock_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    corrected_clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    reviewer_note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
