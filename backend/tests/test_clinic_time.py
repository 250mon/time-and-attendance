"""Tests for clinic-local calendar helpers."""

from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app.core.clinic_time import clinic_today


def test_clinic_today_uses_clinic_timezone():
    """Return the calendar date from datetime.now in the requested timezone."""
    seoul_morning = datetime(2026, 6, 28, 8, 0, tzinfo=ZoneInfo("Asia/Seoul"))
    with patch("app.core.clinic_time.datetime") as mock_datetime:
        mock_datetime.now.return_value = seoul_morning
        assert clinic_today("Asia/Seoul") == date(2026, 6, 28)
