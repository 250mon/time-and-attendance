"""Clinic-local calendar helpers."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def clinic_tz(timezone: str | None = None) -> ZoneInfo:
    """Return ZoneInfo for the given timezone string, defaulting to settings.clinic_timezone."""
    return ZoneInfo(timezone or settings.clinic_timezone)


def clinic_today(timezone: str | None = None) -> date:
    """Return today's date in the clinic timezone (defaults to settings.clinic_timezone)."""
    return datetime.now(clinic_tz(timezone)).date()
