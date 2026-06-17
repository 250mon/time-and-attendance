import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import PunchSource, PunchType


class AttendancePunch(Base):
    __tablename__ = "attendance_punches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    punch_type: Mapped[PunchType] = mapped_column(
        Enum(PunchType, name="punch_type"), nullable=False
    )
    punched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[PunchSource] = mapped_column(
        Enum(PunchSource, name="punch_source"), nullable=False, default=PunchSource.WEB
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    geo_lat: Mapped[float | None] = mapped_column(Numeric(precision=10, scale=7), nullable=True)
    geo_lng: Mapped[float | None] = mapped_column(Numeric(precision=10, scale=7), nullable=True)
    qr_code_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
