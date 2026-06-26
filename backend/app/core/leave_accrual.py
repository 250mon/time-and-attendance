"""
Annual leave accrual engine (Korean LSA Art. 60 + fiscal-year bulk grant).

Separates:
- Legal minimum (hire-date anniversary basis)
- Fiscal policy (fiscal-year bulk grant)
- legal_adjustment top-up when fiscal grants fall below legal minimum
"""

from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Optional

RoundingPolicy = Literal["none", "floor", "ceil", "half_up", "round_2"]
AdjustmentMode = Literal["anniversary_top_up", "termination_only", "none"]


@dataclass(frozen=True)
class LeaveEvent:
    date: date
    days: float
    event_type: str
    basis: str
    note: str = ""


def parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def add_months(d: date, months: int) -> date:
    """Month anniversary; e.g. 2025-01-31 + 1 month → 2025-02-28."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, days_in_month(y, m))
    return date(y, m, day)


def add_years(d: date, years: int) -> date:
    """Year anniversary; Feb 29 → Feb 28 in non-leap years."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def completed_years(start: date, as_of: date) -> int:
    """Completed full years of service as of as_of."""
    years = as_of.year - start.year
    if add_years(start, years) > as_of:
        years -= 1
    return max(0, years)


def regular_annual_leave(completed_service_years: int) -> int:
    """
    Regular annual leave by completed service years (hire-date basis).

    Year 1: 15, year 2: 15, year 3: 16, … capped at 25.
    """
    if completed_service_years < 1:
        return 0
    bonus = max(0, (completed_service_years - 1) // 2)
    return min(15 + bonus, 25)


def round_days(value: float, rounding: RoundingPolicy) -> float:
    if rounding == "none":
        return value
    if rounding == "floor":
        return float(math.floor(value))
    if rounding == "ceil":
        return float(math.ceil(value))
    if rounding == "half_up":
        return math.ceil(value * 2) / 2
    if rounding == "round_2":
        return round(value, 2)
    raise ValueError(f"Unsupported rounding policy: {rounding}")


def fiscal_start_for_year(year: int, fiscal_start_month: int, fiscal_start_day: int) -> date:
    day = min(fiscal_start_day, days_in_month(year, fiscal_start_month))
    return date(year, fiscal_start_month, day)


def fiscal_starts_after_until(
    start_exclusive: date,
    end_inclusive: date,
    fiscal_start_month: int,
    fiscal_start_day: int,
):
    for year in range(start_exclusive.year, end_inclusive.year + 2):
        fs = fiscal_start_for_year(year, fiscal_start_month, fiscal_start_day)
        if start_exclusive < fs <= end_inclusive:
            yield fs


def previous_fiscal_start(
    fiscal_start: date,
    fiscal_start_month: int,
    fiscal_start_day: int,
) -> date:
    return fiscal_start_for_year(
        fiscal_start.year - 1,
        fiscal_start_month,
        fiscal_start_day,
    )


def cumulative_days(events: list[LeaveEvent], on_or_before: date) -> float:
    return sum(e.days for e in events if e.date <= on_or_before)


def serialize_events(events: list[LeaveEvent]) -> list[dict]:
    return [
        {
            "date": e.date.isoformat(),
            "days": round(e.days, 4),
            "event_type": e.event_type,
            "basis": e.basis,
            "note": e.note,
        }
        for e in sorted(events, key=lambda x: (x.date, x.basis, x.event_type))
    ]


def legal_minimum_events(
    hire_date: date,
    effective_as_of: date,
    *,
    assume_full_attendance: bool = True,
) -> list[LeaveEvent]:
    events: list[LeaveEvent] = []

    if effective_as_of < hire_date:
        return events

    for month_index in range(1, 12):
        grant_date = add_months(hire_date, month_index)
        if grant_date <= effective_as_of:
            events.append(
                LeaveEvent(
                    date=grant_date,
                    days=1.0,
                    event_type="monthly_under_one_year",
                    basis="legal_minimum",
                    note=f"{month_index} complete month(s) after hire",
                )
            )

    service_years = completed_years(hire_date, effective_as_of)

    for year in range(1, service_years + 1):
        grant_date = add_years(hire_date, year)
        if grant_date > effective_as_of:
            continue

        if assume_full_attendance:
            days = float(regular_annual_leave(year))
            events.append(
                LeaveEvent(
                    date=grant_date,
                    days=days,
                    event_type="annual_anniversary",
                    basis="legal_minimum",
                    note=f"{year} completed service year(s)",
                )
            )
        else:
            events.append(
                LeaveEvent(
                    date=grant_date,
                    days=0.0,
                    event_type="annual_attendance_unknown",
                    basis="legal_minimum",
                    note="Requires annual attendance rate and monthly perfect-attendance records",
                )
            )

    return sorted(events, key=lambda e: (e.date, e.event_type))


def first_fiscal_prorated_leave(
    hire_date: date,
    grant_date: date,
    *,
    fiscal_start_month: int,
    fiscal_start_day: int,
) -> float:
    prev_start = previous_fiscal_start(
        grant_date,
        fiscal_start_month,
        fiscal_start_day,
    )
    prev_end = grant_date

    service_start = max(hire_date, prev_start)
    service_days = max(0, (prev_end - service_start).days)
    period_days = (prev_end - prev_start).days

    if service_days <= 0 or period_days <= 0:
        return 0.0

    return 15.0 * service_days / period_days


def fiscal_policy_events(
    hire_date: date,
    effective_as_of: date,
    *,
    fiscal_start_month: int = 1,
    fiscal_start_day: int = 1,
    fiscal_rounding: RoundingPolicy = "round_2",
    assume_full_attendance: bool = True,
) -> list[LeaveEvent]:
    events: list[LeaveEvent] = []

    if effective_as_of < hire_date:
        return events

    first_anniversary = add_years(hire_date, 1)
    monthly_cutoff = min(effective_as_of, first_anniversary)

    for month_index in range(1, 12):
        grant_date = add_months(hire_date, month_index)
        if grant_date <= monthly_cutoff:
            events.append(
                LeaveEvent(
                    date=grant_date,
                    days=1.0,
                    event_type="monthly_under_one_year",
                    basis="fiscal_policy",
                    note=f"{month_index} complete month(s) after hire",
                )
            )

    for grant_date in fiscal_starts_after_until(
        hire_date,
        effective_as_of,
        fiscal_start_month,
        fiscal_start_day,
    ):
        if grant_date < first_anniversary:
            raw_days = first_fiscal_prorated_leave(
                hire_date,
                grant_date,
                fiscal_start_month=fiscal_start_month,
                fiscal_start_day=fiscal_start_day,
            )
            days = round_days(raw_days, fiscal_rounding)

            if days > 0:
                events.append(
                    LeaveEvent(
                        date=grant_date,
                        days=days,
                        event_type="fiscal_prorated_first_year",
                        basis="fiscal_policy",
                        note=f"raw={raw_days:.6f}",
                    )
                )
        else:
            service_years_at_fiscal_start = completed_years(hire_date, grant_date)

            if assume_full_attendance:
                days = float(regular_annual_leave(service_years_at_fiscal_start))
                if days > 0:
                    events.append(
                        LeaveEvent(
                            date=grant_date,
                            days=days,
                            event_type="fiscal_regular_annual",
                            basis="fiscal_policy",
                            note=(
                                f"{service_years_at_fiscal_start} completed service year(s) "
                                "at fiscal start"
                            ),
                        )
                    )
            else:
                events.append(
                    LeaveEvent(
                        date=grant_date,
                        days=0.0,
                        event_type="fiscal_attendance_unknown",
                        basis="fiscal_policy",
                        note="Requires attendance records",
                    )
                )

    return sorted(events, key=lambda e: (e.date, e.event_type))


def legal_adjustment_events(
    legal_events: list[LeaveEvent],
    fiscal_events: list[LeaveEvent],
    effective_as_of: date,
    *,
    mode: AdjustmentMode = "anniversary_top_up",
    adjustment_date: Optional[date] = None,
) -> list[LeaveEvent]:
    if mode == "none":
        return []

    adjustments: list[LeaveEvent] = []

    if mode == "termination_only":
        if adjustment_date is None:
            return []
        check_dates = [adjustment_date]
    else:
        check_dates = sorted(
            {e.date for e in legal_events if e.date <= effective_as_of} | {effective_as_of}
        )

    for check_date in check_dates:
        legal_total = cumulative_days(legal_events, check_date)
        fiscal_total = cumulative_days(fiscal_events, check_date)
        adjustment_total = cumulative_days(adjustments, check_date)

        shortage = legal_total - fiscal_total - adjustment_total

        if shortage > 1e-9:
            adjustments.append(
                LeaveEvent(
                    date=check_date,
                    days=shortage,
                    event_type="legal_adjustment",
                    basis="adjustment",
                    note="Top-up so fiscal-year operation is not below legal minimum",
                )
            )

    return adjustments


def calculate_annual_leave(
    hire_date: str | date,
    as_of: str | date,
    *,
    termination_date: str | date | None = None,
    fiscal_start_month: int = 1,
    fiscal_start_day: int = 1,
    fiscal_rounding: RoundingPolicy = "round_2",
    adjustment_mode: AdjustmentMode = "anniversary_top_up",
    assume_full_attendance: bool = True,
) -> dict:
    hire = parse_date(hire_date)
    calc_as_of = parse_date(as_of)
    termination = parse_date(termination_date) if termination_date else None

    if calc_as_of < hire:
        raise ValueError("as_of cannot be earlier than hire_date.")

    if termination is not None and termination < hire:
        raise ValueError("termination_date cannot be earlier than hire_date.")

    effective_as_of = min(calc_as_of, termination) if termination else calc_as_of

    legal = legal_minimum_events(
        hire,
        effective_as_of,
        assume_full_attendance=assume_full_attendance,
    )

    fiscal = fiscal_policy_events(
        hire,
        effective_as_of,
        fiscal_start_month=fiscal_start_month,
        fiscal_start_day=fiscal_start_day,
        fiscal_rounding=fiscal_rounding,
        assume_full_attendance=assume_full_attendance,
    )

    adjustment_date = termination if termination and termination <= calc_as_of else None

    adjustments = legal_adjustment_events(
        legal,
        fiscal,
        effective_as_of,
        mode=adjustment_mode,
        adjustment_date=adjustment_date,
    )

    legal_total = cumulative_days(legal, effective_as_of)
    fiscal_total = cumulative_days(fiscal, effective_as_of)
    adjustment_total = cumulative_days(adjustments, effective_as_of)
    total_after_adjustment = fiscal_total + adjustment_total

    return {
        "hire_date": hire.isoformat(),
        "as_of": calc_as_of.isoformat(),
        "effective_as_of": effective_as_of.isoformat(),
        "termination_date": termination.isoformat() if termination else None,
        "fiscal_year_start": f"{fiscal_start_month:02d}-{fiscal_start_day:02d}",
        "assumptions": {
            "full_attendance": assume_full_attendance,
            "termination_date_is_last_employed_day_inclusive": True,
            "feb_29_anniversary_policy": "Feb 28 in non-leap years",
            "fiscal_proration_denominator": "actual days in prior fiscal year",
            "fiscal_rounding": fiscal_rounding,
            "adjustment_mode": adjustment_mode,
        },
        "summary": {
            "legal_minimum_total": round(legal_total, 4),
            "raw_fiscal_policy_total": round(fiscal_total, 4),
            "legal_adjustment_total": round(adjustment_total, 4),
            "total_after_adjustment": round(total_after_adjustment, 4),
            "shortage_if_settled_now_without_adjustment": round(
                max(0.0, legal_total - fiscal_total),
                4,
            ),
        },
        "legal_minimum_events": serialize_events(legal),
        "fiscal_policy_events": serialize_events(fiscal),
        "adjustment_events": serialize_events(adjustments),
    }


def cumulative_entitlement(
    hire_date: date,
    as_of: date,
    *,
    termination_date: date | None = None,
    fiscal_start_month: int = 1,
    fiscal_start_day: int = 1,
    fiscal_rounding: RoundingPolicy = "round_2",
    adjustment_mode: AdjustmentMode = "anniversary_top_up",
    assume_full_attendance: bool = True,
) -> float:
    if as_of < hire_date:
        return 0.0
    result = calculate_annual_leave(
        hire_date,
        as_of,
        termination_date=termination_date,
        fiscal_start_month=fiscal_start_month,
        fiscal_start_day=fiscal_start_day,
        fiscal_rounding=fiscal_rounding,
        adjustment_mode=adjustment_mode,
        assume_full_attendance=assume_full_attendance,
    )
    return float(result["summary"]["total_after_adjustment"])
