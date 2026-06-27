"""Unit tests for overtime calculation per Permenaker (Indonesian labor regulation)."""
import pytest
from decimal import Decimal

from app.calculations.overtime import (
    calculate_hourly_rate,
    get_multiplier_5day,
    get_multiplier_6day,
    calculate_single_overtime,
    calculate_overtime_total,
    OvertimeEntry,
    HOURLY_DIVISOR,
)
from app.exceptions import OvertimeCalculationError


class TestHourlyRate:
    """Tests for overtime hourly rate calculation (1/173 × monthly salary)."""

    def test_hourly_rate_standard(self):
        """Monthly salary 8,650,000 → hourly = 8,650,000 / 173 = 50,000.00."""
        result = calculate_hourly_rate(Decimal("8650000"))
        assert result == Decimal("50000.00")

    def test_hourly_rate_round_result(self):
        """Monthly salary 10,000,000 → hourly = 10M / 173 ≈ 57,803.47 (rounded to 2dp)."""
        result = calculate_hourly_rate(Decimal("10000000"))
        expected = Decimal("57803.47")
        assert result == expected

    def test_hourly_rate_exact_divisor(self):
        """Monthly salary 173,000 → hourly = 1,000.00."""
        result = calculate_hourly_rate(Decimal("173000"))
        assert result == Decimal("1000.00")


class TestMultiplier5Day:
    """Tests for 5-day work week overtime multipliers."""

    def test_weekday_first_hour(self):
        """Weekday hour 1 = 1.5×."""
        assert get_multiplier_5day(1, "WEEKDAY") == Decimal("1.5")

    def test_weekday_subsequent_hours(self):
        """Weekday hours 2+ = 2×."""
        assert get_multiplier_5day(2, "WEEKDAY") == Decimal("2")
        assert get_multiplier_5day(3, "WEEKDAY") == Decimal("2")

    def test_weekend_hours_1_to_8(self):
        """Weekend hours 1-8 = 2×."""
        for hour in range(1, 9):
            assert get_multiplier_5day(hour, "WEEKEND") == Decimal("2")

    def test_weekend_hour_9(self):
        """Weekend hour 9 = 3×."""
        assert get_multiplier_5day(9, "WEEKEND") == Decimal("3")

    def test_weekend_hour_10_plus(self):
        """Weekend hours 10+ = 4×."""
        assert get_multiplier_5day(10, "WEEKEND") == Decimal("4")
        assert get_multiplier_5day(11, "WEEKEND") == Decimal("4")

    def test_holiday_same_as_weekend(self):
        """Holiday follows same rules as weekend for 5-day week."""
        assert get_multiplier_5day(1, "HOLIDAY") == Decimal("2")
        assert get_multiplier_5day(9, "HOLIDAY") == Decimal("3")
        assert get_multiplier_5day(10, "HOLIDAY") == Decimal("4")


class TestMultiplier6Day:
    """Tests for 6-day work week overtime multipliers."""

    def test_weekday_first_hour(self):
        """Weekday hour 1 = 1.5×."""
        assert get_multiplier_6day(1, "WEEKDAY") == Decimal("1.5")

    def test_weekday_subsequent_hours(self):
        """Weekday hours 2+ = 2×."""
        assert get_multiplier_6day(2, "WEEKDAY") == Decimal("2")

    def test_saturday_hours_1_to_5(self):
        """Saturday (WEEKEND) hours 1-5 = 2×."""
        for hour in range(1, 6):
            assert get_multiplier_6day(hour, "WEEKEND") == Decimal("2")

    def test_saturday_hour_6(self):
        """Saturday (WEEKEND) hour 6 = 3×."""
        assert get_multiplier_6day(6, "WEEKEND") == Decimal("3")

    def test_saturday_hour_7_plus(self):
        """Saturday (WEEKEND) hours 7+ = 4×."""
        assert get_multiplier_6day(7, "WEEKEND") == Decimal("4")
        assert get_multiplier_6day(8, "WEEKEND") == Decimal("4")

    def test_sunday_holiday_hours_1_to_7(self):
        """Sunday/Holiday hours 1-7 = 2×."""
        for hour in range(1, 8):
            assert get_multiplier_6day(hour, "HOLIDAY") == Decimal("2")

    def test_sunday_holiday_hour_8(self):
        """Sunday/Holiday hour 8 = 3×."""
        assert get_multiplier_6day(8, "HOLIDAY") == Decimal("3")

    def test_sunday_holiday_hour_9_plus(self):
        """Sunday/Holiday hours 9+ = 4×."""
        assert get_multiplier_6day(9, "HOLIDAY") == Decimal("4")
        assert get_multiplier_6day(10, "HOLIDAY") == Decimal("4")


class TestSingleOvertime:
    """Tests for single overtime entry calculation."""

    def test_5day_weekday_3_hours(self):
        """5-day week, weekday OT (3 hours).

        Hourly rate: 8,650,000 / 173 = 50,000
        Hour 1: 1.5 × 50,000 = 75,000
        Hour 2: 2 × 50,000 = 100,000
        Hour 3: 2 × 50,000 = 100,000
        Total: 275,000
        """
        hourly_rate = Decimal("50000.00")
        result = calculate_single_overtime(
            hours=Decimal("3"),
            overtime_type="WEEKDAY",
            work_week_type="5_DAY",
            hourly_rate=hourly_rate,
        )
        assert result == Decimal("275000")

    def test_5day_weekend_9_hours(self):
        """5-day week, weekend OT (9 hours).

        Hourly rate: 50,000
        Hours 1-8: 8 × 2 × 50,000 = 800,000
        Hour 9: 3 × 50,000 = 150,000
        Total: 950,000
        """
        hourly_rate = Decimal("50000.00")
        result = calculate_single_overtime(
            hours=Decimal("9"),
            overtime_type="WEEKEND",
            work_week_type="5_DAY",
            hourly_rate=hourly_rate,
        )
        assert result == Decimal("950000")

    def test_6day_saturday_6_hours(self):
        """6-day week, Saturday OT (6 hours).

        Hourly rate: 50,000
        Hours 1-5: 5 × 2 × 50,000 = 500,000
        Hour 6: 3 × 50,000 = 150,000
        Total: 650,000
        """
        hourly_rate = Decimal("50000.00")
        result = calculate_single_overtime(
            hours=Decimal("6"),
            overtime_type="WEEKEND",
            work_week_type="6_DAY",
            hourly_rate=hourly_rate,
        )
        assert result == Decimal("650000")

    def test_6day_sunday_holiday_9_hours(self):
        """6-day week, Sunday/Holiday OT (9 hours).

        Hourly rate: 50,000
        Hours 1-7: 7 × 2 × 50,000 = 700,000
        Hour 8: 3 × 50,000 = 150,000
        Hour 9: 4 × 50,000 = 200,000
        Total: 1,050,000
        """
        hourly_rate = Decimal("50000.00")
        result = calculate_single_overtime(
            hours=Decimal("9"),
            overtime_type="HOLIDAY",
            work_week_type="6_DAY",
            hourly_rate=hourly_rate,
        )
        assert result == Decimal("1050000")

    def test_partial_hours_weekday(self):
        """Partial hours (1.5 hours weekday).

        Hourly rate: 50,000
        Hour 1 (full): 1.5 × 50,000 = 75,000
        0.5 of hour 2: 0.5 × 2 × 50,000 = 50,000
        Total: 125,000
        """
        hourly_rate = Decimal("50000.00")
        result = calculate_single_overtime(
            hours=Decimal("1.5"),
            overtime_type="WEEKDAY",
            work_week_type="5_DAY",
            hourly_rate=hourly_rate,
        )
        assert result == Decimal("125000")

    def test_zero_hours(self):
        """Zero overtime hours → pay = 0."""
        hourly_rate = Decimal("50000.00")
        result = calculate_single_overtime(
            hours=Decimal("0"),
            overtime_type="WEEKDAY",
            work_week_type="5_DAY",
            hourly_rate=hourly_rate,
        )
        assert result == Decimal("0")

    def test_invalid_work_week_type_raises_error(self):
        """Invalid work_week_type should raise OvertimeCalculationError."""
        with pytest.raises(OvertimeCalculationError):
            calculate_single_overtime(
                hours=Decimal("1"),
                overtime_type="WEEKDAY",
                work_week_type="7_DAY",
                hourly_rate=Decimal("50000.00"),
            )

    def test_invalid_overtime_type_raises_error(self):
        """Invalid overtime_type should raise OvertimeCalculationError."""
        with pytest.raises(OvertimeCalculationError):
            calculate_single_overtime(
                hours=Decimal("1"),
                overtime_type="NIGHT",
                work_week_type="5_DAY",
                hourly_rate=Decimal("50000.00"),
            )


class TestOvertimeTotal:
    """Tests for total overtime calculation across multiple entries."""

    def test_multiple_entries(self):
        """Multiple overtime entries in a period.

        Salary: 8,650,000, hourly = 50,000
        Entry 1: Weekday 2 hours → 1.5×50K + 2×50K = 75K + 100K = 175,000
        Entry 2: Weekend 1 hour → 2×50K = 100,000
        Total: 275,000
        """
        entries = [
            OvertimeEntry(overtime_type="WEEKDAY", hours=Decimal("2")),
            OvertimeEntry(overtime_type="WEEKEND", hours=Decimal("1")),
        ]
        result = calculate_overtime_total(
            entries=entries,
            monthly_salary=Decimal("8650000"),
            work_week_type="5_DAY",
        )
        assert result == Decimal("275000")

    def test_empty_entries(self):
        """No overtime entries → total = 0."""
        result = calculate_overtime_total(
            entries=[],
            monthly_salary=Decimal("8650000"),
            work_week_type="5_DAY",
        )
        assert result == Decimal("0")

    def test_negative_salary_raises_error(self):
        """Non-positive salary should raise OvertimeCalculationError."""
        entries = [OvertimeEntry(overtime_type="WEEKDAY", hours=Decimal("1"))]
        with pytest.raises(OvertimeCalculationError):
            calculate_overtime_total(
                entries=entries,
                monthly_salary=Decimal("0"),
                work_week_type="5_DAY",
            )

    def test_single_entry_with_salary(self):
        """Single entry using calculate_overtime_total with standard salary.

        Salary: 8,650,000, hourly = 50,000
        Weekday 3 hours: 75K + 100K + 100K = 275,000
        """
        entries = [OvertimeEntry(overtime_type="WEEKDAY", hours=Decimal("3"))]
        result = calculate_overtime_total(
            entries=entries,
            monthly_salary=Decimal("8650000"),
            work_week_type="5_DAY",
        )
        assert result == Decimal("275000")
