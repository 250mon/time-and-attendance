import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ScheduleStatus


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    user_id: uuid.UUID
    shift_id: uuid.UUID | None
    work_date: date
    scheduled_start: time | None
    scheduled_end: time | None
    scheduled_break_minutes: int
    status: ScheduleStatus
    created_at: datetime
    updated_at: datetime


class ScheduleCreateRequest(BaseModel):
    user_id: uuid.UUID
    shift_id: uuid.UUID | None = None
    work_date: date
    scheduled_start: time | None = None
    scheduled_end: time | None = None
    scheduled_break_minutes: int = Field(default=0, ge=0)
    status: ScheduleStatus = ScheduleStatus.SCHEDULED


class ScheduleUpdateRequest(BaseModel):
    shift_id: uuid.UUID | None = None
    scheduled_start: time | None = None
    scheduled_end: time | None = None
    scheduled_break_minutes: int | None = Field(default=None, ge=0)
    status: ScheduleStatus | None = None


class ScheduleGenerateRequest(BaseModel):
    user_id: uuid.UUID
    shift_id: uuid.UUID
    start_date: date
    end_date: date
    weekdays: list[int] = Field(
        description="Days of the week to schedule: 0=Monday … 6=Sunday",
        min_length=1,
    )

    @model_validator(mode="after")
    def end_after_start(self) -> "ScheduleGenerateRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self
