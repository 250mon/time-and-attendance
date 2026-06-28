import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import ClinicStatus

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
_RESERVED_SLUGS = frozenset(
    {"api", "admin", "www", "health", "me", "static", "assets", "public", "demo"}
)


class ClinicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: ClinicStatus
    timezone: str
    address: str | None
    created_at: datetime
    updated_at: datetime


class ClinicPublicResponse(BaseModel):
    """Minimal public response for slug-lookup — no sensitive fields."""
    model_config = ConfigDict(from_attributes=True)

    name: str
    slug: str


class ClinicCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=3, max_length=64)
    timezone: str = Field(min_length=1, max_length=64)
    address: str | None = None
    owner_name: str = Field(min_length=1, max_length=255)
    owner_email: EmailStr
    owner_password: str = Field(min_length=8, max_length=128)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.lower()
        if not _SLUG_RE.match(v):
            raise ValueError(
                "Slug must be 3–64 characters of lowercase letters, digits, and hyphens; "
                "must not start or end with a hyphen"
            )
        if v in _RESERVED_SLUGS:
            raise ValueError(f"'{v}' is a reserved slug")
        return v


class ClinicUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    address: str | None = None
