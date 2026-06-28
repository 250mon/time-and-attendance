import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import ClinicStatus, EmploymentType, UserRole, UserStatus


class ClinicSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: ClinicStatus
    timezone: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    employment_type: EmploymentType
    hire_date: date | None
    termination_date: date | None
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class AuthUserResponse(UserResponse):
    """Extended user response for /auth/login and /auth/me — includes clinic summary."""
    clinic: ClinicSummary


class StaffCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.STAFF
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    hire_date: date | None = None


class StaffUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    role: UserRole | None = None
    employment_type: EmploymentType | None = None
    hire_date: date | None = None
    termination_date: date | None = None
    status: UserStatus | None = None
