"""
Korean Labor Standards Act (근로기준법) calculations.
"""

from datetime import date


def completed_months_of_service(hire_date: date, as_of: date) -> int:
    """Return fully completed months of continuous service from hire_date up to as_of."""
    months = (as_of.year - hire_date.year) * 12 + (as_of.month - hire_date.month)
    if as_of.day < hire_date.day:
        months -= 1
    return max(0, months)


def annual_leave_entitlement(completed_months: int) -> int:
    """
    Return annual leave days under LSA Art. 60.

    - < 12 completed months : 1 day per completed month (max 11)
    - >= 12 completed months: 15 days base, +1 day per every 2 years beyond
                              the first, capped at 25 days

    Args:
        completed_months: total completed months of continuous service
    """
    if completed_months < 12:
        return min(completed_months, 11)
    years = completed_months // 12
    return min(15 + (years - 1) // 2, 25)
