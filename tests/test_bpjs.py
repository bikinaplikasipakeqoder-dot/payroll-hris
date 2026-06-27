"""Unit tests for BPJS (Badan Penyelenggara Jaminan Sosial) contribution calculation."""
import pytest
from decimal import Decimal

from app.calculations.bpjs import (
    BpjsConfig,
    BpjsResult,
    calculate_bpjs_base,
    calculate_bpjs_contribution,
    calculate_all_bpjs,
)
from app.exceptions import BpjsCalculationError


class TestBpjsBase:
    """Tests for BPJS contribution base calculation."""

    def test_bpjs_base_standard(self):
        """Base salary 10,000,000 + BPJS-eligible allowances 2,000,000 = base 12,000,000."""
        result = calculate_bpjs_base(
            base_salary=Decimal("10000000"),
            allowances_bpjs_base=Decimal("2000000"),
        )
        assert result == Decimal("12000000")

    def test_bpjs_base_no_allowances(self):
        """Base salary only, no BPJS-eligible allowances."""
        result = calculate_bpjs_base(
            base_salary=Decimal("10000000"),
            allowances_bpjs_base=Decimal("0"),
        )
        assert result == Decimal("10000000")

    def test_bpjs_base_zero(self):
        """Zero salary and allowances → base = 0."""
        result = calculate_bpjs_base(
            base_salary=Decimal("0"),
            allowances_bpjs_base=Decimal("0"),
        )
        assert result == Decimal("0")


class TestBpjsContribution:
    """Tests for individual BPJS contribution calculations."""

    def test_contribution_with_cap_kesehatan_employee(self):
        """BPJS Kesehatan employee with salary cap.

        Base 15,000,000, cap 12,000,000
        Effective base = min(15M, 12M) = 12,000,000
        Employee rate 1% → 12M × 0.01 = 120,000
        """
        result = calculate_bpjs_contribution(
            calc_base=Decimal("15000000"),
            rate=Decimal("0.01"),
            max_salary_base=Decimal("12000000"),
        )
        assert result == Decimal("120000")

    def test_contribution_with_cap_kesehatan_employer(self):
        """BPJS Kesehatan employer with salary cap.

        Base 15,000,000, cap 12,000,000
        Effective base = min(15M, 12M) = 12,000,000
        Employer rate 4% → 12M × 0.04 = 480,000
        """
        result = calculate_bpjs_contribution(
            calc_base=Decimal("15000000"),
            rate=Decimal("0.04"),
            max_salary_base=Decimal("12000000"),
        )
        assert result == Decimal("480000")

    def test_contribution_without_cap_jht_employee(self):
        """BPJS JHT employee without salary cap.

        Base 15,000,000, no cap
        Employee rate 2% → 15M × 0.02 = 300,000
        """
        result = calculate_bpjs_contribution(
            calc_base=Decimal("15000000"),
            rate=Decimal("0.02"),
            max_salary_base=None,
        )
        assert result == Decimal("300000")

    def test_contribution_without_cap_jht_employer(self):
        """BPJS JHT employer without salary cap.

        Base 15,000,000, no cap
        Employer rate 3.7% → 15M × 0.037 = 555,000
        """
        result = calculate_bpjs_contribution(
            calc_base=Decimal("15000000"),
            rate=Decimal("0.037"),
            max_salary_base=None,
        )
        assert result == Decimal("555000")

    def test_contribution_with_cap_jp_employee(self):
        """BPJS JP employee with salary cap.

        Base 15,000,000, cap 9,559,600
        Effective base = min(15M, 9,559,600) = 9,559,600
        Employee rate 1% → 9,559,600 × 0.01 = 95,596
        """
        result = calculate_bpjs_contribution(
            calc_base=Decimal("15000000"),
            rate=Decimal("0.01"),
            max_salary_base=Decimal("9559600"),
        )
        assert result == Decimal("95596")

    def test_contribution_with_cap_jp_employer(self):
        """BPJS JP employer with salary cap.

        Base 15,000,000, cap 9,559,600
        Effective base = min(15M, 9,559,600) = 9,559,600
        Employer rate 2% → 9,559,600 × 0.02 = 191,192
        """
        result = calculate_bpjs_contribution(
            calc_base=Decimal("15000000"),
            rate=Decimal("0.02"),
            max_salary_base=Decimal("9559600"),
        )
        assert result == Decimal("191192")

    def test_contribution_base_under_cap(self):
        """When base is under cap, use full base.

        Base 8,000,000, cap 12,000,000
        Effective base = min(8M, 12M) = 8,000,000
        Rate 1% → 80,000
        """
        result = calculate_bpjs_contribution(
            calc_base=Decimal("8000000"),
            rate=Decimal("0.01"),
            max_salary_base=Decimal("12000000"),
        )
        assert result == Decimal("80000")


class TestFullBpjsCalculation:
    """Tests for full BPJS calculation (all types)."""

    def test_all_bpjs_standard(self, sample_bpjs_settings):
        """Full BPJS calculation with standard settings and base 15,000,000.

        KESEHATAN (cap 12M):
          Employee: 12M × 1% = 120,000
          Employer: 12M × 4% = 480,000
        JHT (no cap):
          Employee: 15M × 2% = 300,000
          Employer: 15M × 3.7% = 555,000
        JP (cap 9,559,600):
          Employee: 9,559,600 × 1% = 95,596
          Employer: 9,559,600 × 2% = 191,192
        JKK (employer only, no cap):
          Employer: 15M × 0.24% = 36,000
        JKM (employer only, no cap):
          Employer: 15M × 0.3% = 45,000
        """
        result = calculate_all_bpjs(
            calc_base=Decimal("15000000"),
            bpjs_settings=sample_bpjs_settings,
        )

        assert result.kes_employee == Decimal("120000")
        assert result.kes_employer == Decimal("480000")
        assert result.jht_employee == Decimal("300000")
        assert result.jht_employer == Decimal("555000")
        assert result.jp_employee == Decimal("95596")
        assert result.jp_employer == Decimal("191192")
        assert result.jkk_employer == Decimal("36000")
        assert result.jkm_employer == Decimal("45000")

    def test_all_bpjs_total_employee(self, sample_bpjs_settings):
        """Verify total_employee property sums KES + JHT + JP employee."""
        result = calculate_all_bpjs(
            calc_base=Decimal("15000000"),
            bpjs_settings=sample_bpjs_settings,
        )
        expected_total = Decimal("120000") + Decimal("300000") + Decimal("95596")
        assert result.total_employee == expected_total

    def test_all_bpjs_total_employer(self, sample_bpjs_settings):
        """Verify total_employer property sums all employer contributions."""
        result = calculate_all_bpjs(
            calc_base=Decimal("15000000"),
            bpjs_settings=sample_bpjs_settings,
        )
        expected_total = (
            Decimal("480000")
            + Decimal("555000")
            + Decimal("191192")
            + Decimal("36000")
            + Decimal("45000")
        )
        assert result.total_employer == expected_total

    def test_all_bpjs_base_under_all_caps(self, sample_bpjs_settings):
        """When base is under all caps, no capping is applied.

        Base 8,000,000 (under KESEHATAN cap 12M and JP cap 9.5M)
        """
        result = calculate_all_bpjs(
            calc_base=Decimal("8000000"),
            bpjs_settings=sample_bpjs_settings,
        )
        assert result.kes_employee == Decimal("80000")  # 8M × 1%
        assert result.jht_employee == Decimal("160000")  # 8M × 2%
        assert result.jp_employee == Decimal("80000")  # 8M × 1% (under JP cap)

    def test_all_bpjs_negative_base_raises_error(self, sample_bpjs_settings):
        """Negative BPJS base should raise BpjsCalculationError."""
        with pytest.raises(BpjsCalculationError):
            calculate_all_bpjs(
                calc_base=Decimal("-1000000"),
                bpjs_settings=sample_bpjs_settings,
            )

    def test_all_bpjs_missing_type_returns_zero(self):
        """Missing BPJS type in settings returns 0 for that type."""
        partial_settings = {
            "KESEHATAN": BpjsConfig(
                bpjs_type="KESEHATAN",
                employee_rate=Decimal("0.01"),
                employer_rate=Decimal("0.04"),
                max_salary_base=Decimal("12000000"),
            ),
        }
        result = calculate_all_bpjs(
            calc_base=Decimal("10000000"),
            bpjs_settings=partial_settings,
        )
        assert result.kes_employee == Decimal("100000")
        assert result.jht_employee == Decimal("0")
        assert result.jp_employee == Decimal("0")
        assert result.jkk_employer == Decimal("0")
        assert result.jkm_employer == Decimal("0")
