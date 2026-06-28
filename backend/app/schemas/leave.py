import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import LeaveStatus


class LeaveTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    default_days_per_year: int | None
    requires_approval: bool
    tenure_based: bool
    allow_carryover: bool
    carryover_max_days: int | None
    active: bool
    created_at: datetime
    updated_at: datetime


class LeaveTypeCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    default_days_per_year: int | None = Field(
        None,
        ge=1,
        le=365,
        description="Annual leave: unused. Other types: max days per single request (blank = no limit).",
    )
    requires_approval: bool = True
    tenure_based: bool = False
    allow_carryover: bool = False
    carryover_max_days: int | None = Field(None, ge=1, le=365)


class LeaveTypeUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    default_days_per_year: int | None = Field(
        None,
        ge=1,
        le=365,
        description="Annual leave: unused. Other types: max days per single request (blank = no limit).",
    )
    requires_approval: bool | None = None
    tenure_based: bool | None = None
    allow_carryover: bool | None = None
    carryover_max_days: int | None = Field(None, ge=1, le=365)
    active: bool | None = None


class LeaveRequestCreateRequest(BaseModel):
    leave_type_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def end_after_start(self) -> "LeaveRequestCreateRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class ReviewLeaveRequest(BaseModel):
    reviewer_note: str | None = Field(None, max_length=500)


class LeaveRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    user_id: uuid.UUID
    leave_type_id: uuid.UUID
    reviewer_id: uuid.UUID | None
    start_date: date
    end_date: date
    total_days: int
    reason: str | None
    status: LeaveStatus
    reviewer_note: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    exceeds_per_request_max: bool = False
    max_days_per_request: int | None = None
    policy_warning: str | None = None

    @classmethod
    def from_request(cls, req: object, leave_type: object | None) -> "LeaveRequestResponse":
        from app.services.leave_request_service import per_request_max_warning

        exceeded = False
        max_days: int | None = None
        warning: str | None = None

        if leave_type is not None:
            warning = per_request_max_warning(leave_type, req.total_days)  # type: ignore[attr-defined]
            exceeded = warning is not None
            if not leave_type.tenure_based:  # type: ignore[attr-defined]
                max_days = leave_type.default_days_per_year  # type: ignore[attr-defined]

        data = cls.model_validate(req).model_dump()
        data.update(
            exceeds_per_request_max=exceeded,
            max_days_per_request=max_days,
            policy_warning=warning,
        )
        return cls(**data)
