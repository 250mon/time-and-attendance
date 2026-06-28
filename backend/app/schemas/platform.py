import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import ClinicStatus


class PlatformClinicUpdateRequest(BaseModel):
    name: str | None = None
    timezone: str | None = None
    address: str | None = None
    owner_name: str | None = None
    owner_email: EmailStr | None = None
    owner_password: str | None = Field(default=None, min_length=8, max_length=128)


class PlatformClinicResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: ClinicStatus
    timezone: str
    address: str | None
    user_count: int
    created_at: datetime
    updated_at: datetime


class PlatformMetricsResponse(BaseModel):
    total_clinics: int
    active_clinics: int
    suspended_clinics: int
    total_users: int
