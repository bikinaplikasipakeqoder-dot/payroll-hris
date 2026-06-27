"""
Overtime calculation per Permenaker (Indonesian labor regulation).
All functions are PURE — no DB access, no side effects.

Hourly rate = 1/173 × monthly_salary (standard for all work week types)

Multipliers:
5-DAY WORK WEEK:
  Weekday: 1st hour = 1.5×, 2nd+ hours = 2×
  Weekend/Holiday: 1-8th hours = 2×, 9th hour = 3×, 10th+ hours = 4×

6-DAY WORK WEEK:
  Weekday: 1st hour = 1.5×, 2nd+ hours = 2×
  Saturday: 1-5th hours = 2×, 6th hour = 3×, 7th+ hours = 4×
  Sunday/Holiday: 1-7th hours = 2×, 8th hour = 3×, 9th+ hours = 4×

Reference: PP 35/2021, Kepmenaker 102/MEN/VI/2004
"""
from decimal import Decimal
from typing import List
from dataclasses import dataclass

HOURLY_DIVISOR = Decimal("173")


@dataclass
class OvertimeEntry:
    """Represents a single overtime record for calculation."""

    overtime_type: str  # WEEKDAY, WEEKEND, HOLIDAY
    hours: Decimal


def calculate_hourly_rate(monthly_salary: Decimal) -> Decimal:
    """Calculate overtime hourly rate: 1/173 × monthly salary.

    Per Kepmenaker 102/MEN/VI/2004: The divisor 173 is used for all
    work week types (both 5-day and 6-day).

    Args:
        monthly_salary: Monthly base salary for hourly rate calculation

    Returns:
        Hourly rate rounded to 2 decimal places for intermediate calculation
    """
    from app.utils.decimal_utils import round_calc

    return round_calc(monthly_salary / HOURLY_DIVISOR)


def get_multiplier_5day(hour_index: int, overtime_type: str) -> Decimal:
    """Get overtime multiplier for 5-day work week.

    Per PP 35/2021:
    - Weekday: 1st hour = 1.5×, subsequent hours = 2×
    - Weekend/Holiday: hours 1-8 = 2×, hour 9 = 3×, hour 10+ = 4×

    Args:
        hour_index: 1-based hour number (1st hour, 2nd hour, etc.)
        overtime_type: WEEKDAY, WEEKEND, or HOLIDAY
    """
    if overtime_type == "WEEKDAY":
        if hour_index == 1:
            return Decimal("1.5")
        else:
            return Decimal("2")
    else:  # WEEKEND or HOLIDAY
        if hour_index <= 8:
            return Decimal("2")
        elif hour_index == 9:
            return Decimal("3")
        else:
            return Decimal("4")


def get_multiplier_6day(hour_index: int, overtime_type: str) -> Decimal:
    """Get overtime multiplier for 6-day work week.

    Per PP 35/2021:
    - Weekday: 1st hour = 1.5×, subsequent hours = 2×
    - Saturday (WEEKEND): hours 1-5 = 2×, hour 6 = 3×, hour 7+ = 4×
    - Sunday/Holiday (HOLIDAY): hours 1-7 = 2×, hour 8 = 3×, hour 9+ = 4×

    Args:
        hour_index: 1-based hour number
        overtime_type: WEEKDAY, WEEKEND (Saturday), or HOLIDAY (Sunday/Holiday)
    """
    if overtime_type == "WEEKDAY":
        if hour_index == 1:
            return Decimal("1.5")
        else:
            return Decimal("2")
    elif overtime_type == "WEEKEND":  # Saturday for 6-day week
        if hour_index <= 5:
            return Decimal("2")
        elif hour_index == 6:
            return Decimal("3")
        else:
            return Decimal("4")
    else:  # HOLIDAY (Sunday for 6-day week)
        if hour_index <= 7:
            return Decimal("2")
        elif hour_index == 8:
            return Decimal("3")
        else:
            return Decimal("4")


def calculate_single_overtime(
    hours: Decimal, overtime_type: str, work_week_type: str, hourly_rate: Decimal
) -> Decimal:
    """Calculate overtime pay for a single overtime entry.

    Applies hour-by-hour multipliers according to Permenaker rules.
    Supports partial hours for the last hour of overtime.

    Args:
        hours: Total overtime hours (supports fractional, e.g., 2.5)
        overtime_type: WEEKDAY, WEEKEND, or HOLIDAY
        work_week_type: "5_DAY" or "6_DAY"
        hourly_rate: Pre-calculated hourly rate (1/173 × salary)

    Returns:
        Overtime pay for this entry (rounded to nearest Rupiah)

    Raises:
        OvertimeCalculationError: If overtime_type or work_week_type is invalid
    """
    from app.utils.decimal_utils import round_money
    from app.exceptions import OvertimeCalculationError

    if work_week_type not in ("5_DAY", "6_DAY"):
        raise OvertimeCalculationError(
            f"Invalid work_week_type: {work_week_type}. Must be '5_DAY' or '6_DAY'."
        )

    if overtime_type not in ("WEEKDAY", "WEEKEND", "HOLIDAY"):
        raise OvertimeCalculationError(
            f"Invalid overtime_type: {overtime_type}. Must be 'WEEKDAY', 'WEEKEND', or 'HOLIDAY'."
        )

    get_multiplier = (
        get_multiplier_5day if work_week_type == "5_DAY" else get_multiplier_6day
    )
    total = Decimal("0")

    # Process each hour (handle partial hours for the last hour)
    full_hours = int(hours)
    partial = hours - Decimal(str(full_hours))

    for i in range(1, full_hours + 1):
        multiplier = get_multiplier(i, overtime_type)
        total += hourly_rate * multiplier

    # Handle partial last hour
    if partial > Decimal("0"):
        next_hour_index = full_hours + 1
        multiplier = get_multiplier(next_hour_index, overtime_type)
        total += hourly_rate * multiplier * partial

    return round_money(total)


def calculate_overtime_total(
    entries: List[OvertimeEntry], monthly_salary: Decimal, work_week_type: str
) -> Decimal:
    """Calculate total overtime pay for all entries in a period.

    Args:
        entries: List of overtime entries (type + hours)
        monthly_salary: Monthly salary for hourly rate calculation
        work_week_type: "5_DAY" or "6_DAY"

    Returns:
        Total overtime pay for the period (rounded to nearest Rupiah)

    Raises:
        OvertimeCalculationError: If monthly_salary is non-positive
    """
    from app.utils.decimal_utils import round_money
    from app.exceptions import OvertimeCalculationError

    if not entries:
        return Decimal("0")

    if monthly_salary <= Decimal("0"):
        raise OvertimeCalculationError(
            f"Monthly salary must be positive for overtime calculation: {monthly_salary}"
        )

    hourly_rate = calculate_hourly_rate(monthly_salary)
    total = Decimal("0")

    for entry in entries:
        total += calculate_single_overtime(
            entry.hours, entry.overtime_type, work_week_type, hourly_rate
        )

    return round_money(total)
