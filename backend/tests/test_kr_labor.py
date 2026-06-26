from datetime import date
from decimal import Decimal

import pytest

from app.core.kr_labor import (
    annual_leave_for_calendar_year,
    as_of_date_for_balance_year,
    completed_months_of_service,
)


@pytest.mark.parametrize("hire, as_of, expected", [
    (date(2023, 3, 15), date(2024, 3, 15), 12),
    (date(2023, 3, 15), date(2024, 3, 14), 11),
    (date(2020, 6, 1), date(2026, 1, 1), 67),
    (date(2027, 1, 1), date(2026, 1, 1), 0),
    (date(2024, 5, 10), date(2024, 5, 10), 0),
])
def test_completed_months_of_service(hire, as_of, expected):
    assert completed_months_of_service(hire, as_of) == expected


def test_hire_year_monthly_accrual_only():
    hire = date(2025, 6, 13)
    assert annual_leave_for_calendar_year(hire, 2025, date(2025, 7, 13)) == Decimal("1.0")
    assert annual_leave_for_calendar_year(hire, 2025, date(2025, 12, 31)) == Decimal("6.0")


def test_calendar_year_before_hire():
    assert annual_leave_for_calendar_year(date(2025, 3, 15), 2024) == Decimal("0")


def test_june_27_2025_hire_pre_anniversary_uses_monthly_only():
    """Before 1-year anniversary, calendar-year balance is monthly 월차 only."""
    hire = date(2025, 6, 27)
    assert annual_leave_for_calendar_year(hire, 2025, date(2025, 12, 31)) == Decimal("6.0")
    assert annual_leave_for_calendar_year(hire, 2026, date(2026, 6, 26)) == Decimal("5.0")


def test_june_27_2025_hire_post_anniversary_includes_fiscal_and_top_up():
    """After anniversary, calendar-year balance includes Jan grant and adjustments."""
    hire = date(2025, 6, 27)
    total = annual_leave_for_calendar_year(hire, 2026, date(2026, 12, 31))
    assert total > Decimal("15.0")


def test_kim_minji_2025_pre_anniversary_monthly_only():
    hire = date(2024, 6, 13)
    assert annual_leave_for_calendar_year(hire, 2025, date(2025, 6, 12)) == Decimal("5.0")


def test_kim_minji_2025_includes_anniversary_top_up():
    """
    Hired 2024-06-13: 2025 includes Jan proration, monthly, and legal_adjustment
    at the 1-year anniversary — not fiscal-only 8.8.
    """
    hire = date(2024, 6, 13)
    total = annual_leave_for_calendar_year(hire, 2025, date(2025, 12, 31))
    assert total > Decimal("8.8")
    assert total >= Decimal("19.0")


def test_kim_minji_2026_regular_fiscal_grant():
    """Hired 2024-06-13: 2026 Jan 1 regular grant year."""
    hire = date(2024, 6, 13)
    total = annual_leave_for_calendar_year(hire, 2026, date(2026, 6, 26))
    assert total >= Decimal("15.0")


def test_as_of_date_for_balance_year():
    today = date(2026, 6, 26)
    assert as_of_date_for_balance_year(2025, today) == date(2025, 12, 31)
    assert as_of_date_for_balance_year(2026, today) == date(2026, 6, 26)
    assert as_of_date_for_balance_year(2027, today) == date(2027, 1, 1)


def test_july_hire_2026_calendar_year_with_top_up():
    """2025-07-01 hire: 2026 includes proration, late monthly, anniversary + adjustment."""
    hire = date(2025, 7, 1)
    total = annual_leave_for_calendar_year(hire, 2026, date(2026, 12, 31))
    # 26 cumulative at year-end minus 5 monthly days already granted in 2025
    assert total == Decimal("21.0")
