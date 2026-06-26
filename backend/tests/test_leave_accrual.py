"""Tests for leave_accrual engine (legal minimum + fiscal policy + adjustment)."""

from datetime import date

import pytest

from app.core.leave_accrual import (
    add_months,
    add_years,
    calculate_annual_leave,
    completed_years,
    cumulative_entitlement,
    regular_annual_leave,
)


def test_regular_annual_leave_table():
    assert regular_annual_leave(0) == 0
    assert regular_annual_leave(1) == 15
    assert regular_annual_leave(2) == 15
    assert regular_annual_leave(3) == 16
    assert regular_annual_leave(4) == 16
    assert regular_annual_leave(5) == 17
    assert regular_annual_leave(21) == 25
    assert regular_annual_leave(30) == 25


def test_completed_years():
    hire = date(2025, 7, 1)
    assert completed_years(hire, date(2026, 6, 30)) == 0
    assert completed_years(hire, date(2026, 7, 1)) == 1
    assert completed_years(hire, date(2027, 7, 1)) == 2


def test_add_months_end_of_month():
    assert add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)


def test_add_years_feb_29():
    assert add_years(date(2024, 2, 29), 1) == date(2025, 2, 28)


def test_example_july_hire_anniversary_top_up():
    """2025-07-01 hire, as_of 2026-07-01 — legal 26 vs fiscal 18.56, adjustment 7.44."""
    result = calculate_annual_leave(
        hire_date="2025-07-01",
        as_of="2026-07-01",
        fiscal_start_month=1,
        fiscal_start_day=1,
        fiscal_rounding="none",
        adjustment_mode="anniversary_top_up",
    )
    summary = result["summary"]
    assert summary["legal_minimum_total"] == 26.0
    assert summary["raw_fiscal_policy_total"] == pytest.approx(18.5616, rel=1e-3)
    assert summary["legal_adjustment_total"] == pytest.approx(7.4384, rel=1e-3)
    assert summary["total_after_adjustment"] == pytest.approx(26.0, rel=1e-3)
    assert any(e["event_type"] == "legal_adjustment" for e in result["adjustment_events"])


def test_example_terminate_before_anniversary_no_15_day_legal():
    """2026-06-30 termination — no 1-year anniversary grant; fiscal already covers legal."""
    result = calculate_annual_leave(
        hire_date="2025-07-01",
        as_of="2026-06-30",
        termination_date="2026-06-30",
        fiscal_rounding="none",
        adjustment_mode="termination_only",
    )
    summary = result["summary"]
    assert summary["legal_minimum_total"] == 11.0
    assert summary["raw_fiscal_policy_total"] == pytest.approx(18.5616, rel=1e-3)
    assert summary["legal_adjustment_total"] == 0.0
    assert summary["shortage_if_settled_now_without_adjustment"] == 0.0


def test_example_terminate_after_anniversary_settlement():
    """2026-10-01 termination — 15-day anniversary occurred; settlement needed."""
    result = calculate_annual_leave(
        hire_date="2025-07-01",
        as_of="2026-10-01",
        termination_date="2026-10-01",
        fiscal_rounding="none",
        adjustment_mode="termination_only",
    )
    summary = result["summary"]
    assert summary["legal_minimum_total"] == 26.0
    assert summary["legal_adjustment_total"] == pytest.approx(7.4384, rel=1e-3)
    assert summary["total_after_adjustment"] == pytest.approx(26.0, rel=1e-3)


def test_fiscal_proration_uses_actual_fiscal_days():
    """2025-07-01 hire → 2026-01-01 grant uses 184/365 days."""
    result = calculate_annual_leave(
        hire_date="2025-07-01",
        as_of="2026-01-01",
        fiscal_rounding="none",
        adjustment_mode="none",
    )
    fiscal = result["fiscal_policy_events"]
    prorated = next(e for e in fiscal if e["event_type"] == "fiscal_prorated_first_year")
    assert prorated["days"] == pytest.approx(15 * 184 / 365, rel=1e-4)


def test_jan_1_hire_gets_regular_grant_next_fiscal_year():
    """Hire on fiscal start day → next fiscal year regular 15 (not prorated)."""
    result = calculate_annual_leave(
        hire_date="2025-01-01",
        as_of="2026-01-01",
        fiscal_rounding="round_2",
        adjustment_mode="none",
    )
    fiscal = result["fiscal_policy_events"]
    regular = [e for e in fiscal if e["event_type"] == "fiscal_regular_annual"]
    assert len(regular) == 1
    assert regular[0]["days"] == 15.0


def test_cumulative_entitlement_before_hire():
    assert cumulative_entitlement(date(2025, 7, 1), date(2025, 6, 30)) == 0.0
