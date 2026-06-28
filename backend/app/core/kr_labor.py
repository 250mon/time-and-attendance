"""
Korean Labor Standards Act (근로기준법) — calendar-year balance facade.

Delegates to leave_accrual for legal minimum + fiscal policy + legal_adjustment.
"""

from datetime import date, timedelta
from decimal import Decimal

from typing import cast

from app.core.clinic_time import clinic_today
from app.core.config import settings
from app.core.leave_accrual import (
    AdjustmentMode,
    RoundingPolicy,
    add_years,
    cumulative_entitlement,
    legal_minimum_events,
)


def completed_months_of_service(hire_date: date, as_of: date) -> int:
    """Return fully completed months of continuous service from hire_date up to as_of."""
    months = (as_of.year - hire_date.year) * 12 + (as_of.month - hire_date.month)
    if as_of.day < hire_date.day:
        months -= 1
    return max(0, months)


def _leave_options(
    *,
    fiscal_start_month: int | None = None,
    fiscal_start_day: int | None = None,
    fiscal_rounding: RoundingPolicy | None = None,
    adjustment_mode: AdjustmentMode | None = None,
) -> dict:
    return {
        "fiscal_start_month": fiscal_start_month or settings.leave_fiscal_start_month,
        "fiscal_start_day": fiscal_start_day or settings.leave_fiscal_start_day,
        "fiscal_rounding": cast(
            RoundingPolicy,
            fiscal_rounding or settings.leave_fiscal_rounding,
        ),
        "adjustment_mode": cast(
            AdjustmentMode,
            adjustment_mode or settings.leave_adjustment_mode,
        ),
    }


def annual_leave_for_calendar_year(
    hire_date: date,
    year: int,
    as_of: date | None = None,
    termination_date: date | None = None,
    *,
    fiscal_start_month: int | None = None,
    fiscal_start_day: int | None = None,
    fiscal_rounding: RoundingPolicy | None = None,
    adjustment_mode: AdjustmentMode | None = None,
) -> Decimal:
    """
    Entitlement granted during calendar `year` (fiscal grants + monthly + legal_adjustment).

    Computed as the increase in cumulative total_after_adjustment during that year.
    """
    if year < hire_date.year:
        return Decimal("0")

    opts = _leave_options(
        fiscal_start_month=fiscal_start_month,
        fiscal_start_day=fiscal_start_day,
        fiscal_rounding=fiscal_rounding,
        adjustment_mode=adjustment_mode,
    )
    today = as_of or clinic_today()

    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    if year < today.year:
        effective_end = year_end
    elif year == today.year:
        effective_end = min(today, year_end)
    else:
        effective_end = year_start

    if effective_end < hire_date:
        return Decimal("0")

    if termination_date is not None:
        effective_end = min(effective_end, termination_date)
        if effective_end < hire_date:
            return Decimal("0")

    first_anniversary = add_years(hire_date, 1)
    if effective_end < first_anniversary:
        # Before the 1-year anniversary only monthly 월차 accrues; Jan 1 fiscal
        # proration and anniversary grants are settled once the year is complete.
        events = legal_minimum_events(hire_date, effective_end)
        monthly_days = sum(
            e.days
            for e in events
            if e.event_type == "monthly_under_one_year"
            and year_start <= e.date <= effective_end
        )
        return Decimal(str(round(monthly_days, 1)))

    day_before = year_start - timedelta(days=1)
    prior = (
        0.0
        if day_before < hire_date
        else cumulative_entitlement(
            hire_date,
            day_before,
            termination_date=termination_date,
            **opts,
        )
    )
    current = cumulative_entitlement(
        hire_date,
        effective_end,
        termination_date=termination_date,
        **opts,
    )

    return Decimal(str(round(max(0.0, current - prior), 1)))


def as_of_date_for_balance_year(year: int, today: date | None = None) -> date:
    """Pick the reference date for recalculating a calendar-year balance."""
    today = today or clinic_today()
    if year < today.year:
        return date(year, 12, 31)
    if year == today.year:
        return today
    return date(year, 1, 1)
