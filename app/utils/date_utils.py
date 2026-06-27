from datetime import date, timedelta
import calendar


def get_month_range(year: int, month: int) -> tuple[date, date]:
    """Get first and last day of a month."""
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    return first_day, last_day


def is_december(period_date: date) -> bool:
    """Check if the period is December (for TER year-end reconciliation)."""
    return period_date.month == 12


def get_month_number(period_start: date) -> int:
    """Get month number (1-12) from period start date."""
    return period_start.month


def days_in_period(start_date: date, end_date: date) -> int:
    """Calculate number of days in a period (inclusive)."""
    return (end_date - start_date).days + 1


def parse_payroll_period(period_str: str) -> tuple[int, int]:
    """Parse payroll period string (YYYY-MM) into year and month."""
    parts = period_str.split("-")
    return int(parts[0]), int(parts[1])
