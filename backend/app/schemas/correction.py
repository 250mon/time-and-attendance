import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import CorrectionStatus

_TIME_RE = r"^\d{2}:\d{2}$"


class CorrectionCreateRequest(BaseModel):
    work_date: date
    corrected_clock_in: str | None = Field(None, pattern=_TIME_RE, description="HH:MM in clinic local time")
    corrected_clock_out: str | None = Field(None, pattern=_TIME_RE, description="HH:MM in clinic local time")
    reason: str = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def at_least_one_time(self) -> "CorrectionCreateRequest":
        if self.corrected_clock_in is None and self.corrected_clock_out is None:
            raise ValueError("At least one of corrected_clock_in or corrected_clock_out must be provided.")
        return self


class ReviewRequest(BaseModel):
    reviewer_note: str | None = Field(None, max_length=500)


class CorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    user_id: uuid.UUID
    reviewer_id: uuid.UUID | None
    work_date: date
    status: CorrectionStatus
    corrected_clock_in: datetime | None
    corrected_clock_out: datetime | None
    reason: str
    reviewer_note: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
