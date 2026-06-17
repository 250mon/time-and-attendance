from datetime import date

import pytest

from app.core.kr_labor import annual_leave_entitlement, completed_months_of_service


@pytest.mark.parametrize("months,expected", [
    # < 1 year: 1 day per completed month
    (0, 0),
    (1, 1),
    (6, 6),
    (11, 11),
    # 1st year: 15 days
    (12, 15),
    # 2nd year: still 15 (extra days start at year 3)
    (23, 15),
    (24, 15),
    (35, 15),
    # 3rd year: 16
    (36, 16),
    (47, 16),
    # 4th year: 16
    (48, 16),
    # 5th year: 17
    (60, 17),
    # 21st year: 25 (cap) — 252 months
    (252, 25),
    # beyond cap stays at 25
    (360, 25),
])
def test_annual_leave_entitlement(months, expected):
    assert annual_leave_entitlement(months) == expected


@pytest.mark.parametrize("hire, as_of, expected", [
    # exact month boundary
    (date(2023, 3, 15), date(2024, 3, 15), 12),
    # day not yet reached — one month short
    (date(2023, 3, 15), date(2024, 3, 14), 11),
    # start of year calculation used for balance allocation
    (date(2020, 6, 1),  date(2026, 1, 1),  67),  # 5y 7m = 67
    # hired after as_of → 0
    (date(2027, 1, 1),  date(2026, 1, 1),  0),
    # same day → 0 completed months
    (date(2024, 5, 10), date(2024, 5, 10), 0),
])
def test_completed_months_of_service(hire, as_of, expected):
    assert completed_months_of_service(hire, as_of) == expected


def test_sub_one_year_accrual_grows_monthly():
    """
    A worker hired mid-year accrues 1 day per completed month.
    Each month anniversary the entitlement increases by 1.
    """
    hire = date(2025, 6, 13)
    cases = [
        (date(2025, 6, 13), 0),   # hire day — 0 completed months
        (date(2025, 7, 12), 0),   # one day before first anniversary
        (date(2025, 7, 13), 1),   # first month complete
        (date(2025, 8, 13), 2),
        (date(2025, 12, 13), 6),  # 6 months
        (date(2026, 5, 13), 11),  # 11 months — still < 1 year
        (date(2026, 6, 13), 15),  # 12 months complete — jumps to 15 days (LSA Art. 60 §1)
    ]
    for as_of, expected_days in cases:
        months = completed_months_of_service(hire, as_of)
        assert annual_leave_entitlement(months) == expected_days, (
            f"as_of={as_of}: expected {expected_days} days, "
            f"got {annual_leave_entitlement(months)} (months={months})"
        )
