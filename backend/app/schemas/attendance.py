import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AttendanceDayStatus, PunchSource, PunchType
from app.schemas.schedule import ScheduleResponse


class PunchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    user_id: uuid.UUID
    punch_type: PunchType
    punched_at: datetime
    source: PunchSource
    ip_address: str | None
    created_at: datetime


class TodayStatusResponse(BaseModel):
    work_date: date
    is_clocked_in: bool
    punches: list[PunchResponse]
    schedule: ScheduleResponse | None
    last_punch: PunchResponse | None


class UserDayPunches(BaseModel):
    user_id: uuid.UUID
    user_name: str
    punches: list[PunchResponse]
    is_clocked_in: bool


class AttendanceDayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    user_id: uuid.UUID
    work_date: date
    status: AttendanceDayStatus
    scheduled_minutes: int | None
    actual_clock_in: datetime | None
    actual_clock_out: datetime | None
    worked_minutes: int
    regular_minutes: int
    overtime_minutes: int
    late_minutes: int
    early_leave_minutes: int
    break_minutes: int
    is_locked: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
