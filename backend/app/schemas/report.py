import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AttendanceDayStatus


class AttendanceSummaryRow(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    user_id: uuid.UUID
    user_name: str
    user_email: str
    total_records: int
    days_present: int
    days_absent: int
    days_on_leave: int
    days_holiday: int
    worked_hours: float
    overtime_hours: float
    late_minutes: int
    early_leave_minutes: int


class LeaveSummaryRow(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    user_id: uuid.UUID
    user_name: str
    leave_type_id: uuid.UUID
    leave_type_name: str
    year: int
    balance_days: float
    used_days: float
    remaining_days: float


class MonthlyDetailRow(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    work_date: date
    user_id: uuid.UUID
    user_name: str
    status: AttendanceDayStatus
    actual_clock_in: datetime | None
    actual_clock_out: datetime | None
    worked_minutes: int
    worked_hours: float
    overtime_minutes: int
    late_minutes: int
    early_leave_minutes: int
    is_locked: bool
