import uuid
from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field


class ShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    start_time: time
    end_time: time
    break_minutes: int
    crosses_midnight: bool
    active: bool
    created_at: datetime
    updated_at: datetime


class ShiftCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    start_time: time
    end_time: time
    break_minutes: int = Field(default=0, ge=0)
    crosses_midnight: bool = False


class ShiftUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    start_time: time | None = None
    end_time: time | None = None
    break_minutes: int | None = Field(default=None, ge=0)
    crosses_midnight: bool | None = None
    active: bool | None = None
