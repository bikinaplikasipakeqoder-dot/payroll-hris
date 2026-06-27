"""Unit tests for PPh 21 Pasal 17 progressive tax calculation engine."""
import pytest
from decimal import Decimal

from app.calculations.pph21_pasal17 import (
    TaxBracket,
    calculate_biaya_jabatan,
    calculate_annual_bpjs_deductible,
    calculate_pkp,
    apply_progressive_brackets,
    calculate_monthly_pph21_pasal17,
)


class TestBiayaJabatan:
    """Tests for biaya jabatan (occupational expense deduction) calculation."""

    def test_biaya_jabatan_hits_cap(self):
        """Annual gross 120,000,000 → biaya jabatan = 6,000,000 (hits 5% cap at 6M)."""
        annual_gross = Decimal("120000000")
        result = calculate_biaya_jabatan(annual_gross)
        assert result == Decimal("6000000")

    def test_biaya_jabatan_under_cap(self):
        """Annual gross 60,000,000 → biaya jabatan = 3,000,000 (5% = 3M, under 6M cap)."""
        annual_gross = Decimal("60000000")
        result = calculate_biaya_jabatan(annual_gross)
        assert result == Decimal("3000000")

    def test_biaya_jabatan_exactly_at_cap(self):
        """Annual gross exactly 120,000,000 → 5% = 6,000,000 = cap."""
        annual_gross = Decimal("120000000")
        result = calculate_biaya_jabatan(annual_gross)
        assert result == Decimal("6000000")

    def test_biaya_jabatan_above_cap(self):
        """Annual gross 240,000,000 → 5% would be 12M, but capped at 6M."""
        annual_gross = Decimal("240000000")
        result = calculate_biaya_jabatan(annual_gross)
        assert result == Decimal("6000000")

    def test_biaya_jabatan_zero_income(self):
        """Annual gross 0 → biaya jabatan = 0."""
        result = calculate_biaya_jabatan(Decimal("0"))
        assert result == Decimal("0")


class TestAnnualBpjsDeductible:
    """Tests for annual BPJS deductible (JHT + JP employee) calculation."""

    def test_annual_bpjs_deductible(self):
        """Monthly JHT emp 200,000 + JP emp 100,000 → annual = 3,600,000."""
        result = calculate_annual_bpjs_deductible(
            monthly_jht_employee=Decimal("200000"),
            monthly_jp_employee=Decimal("100000"),
        )
        assert result == Decimal("3600000")

    def test_annual_bpjs_deductible_zero(self):
        """No BPJS contributions → annual deductible = 0."""
        result = calculate_annual_bpjs_deductible(
            monthly_jht_employee=Decimal("0"),
            monthly_jp_employee=Decimal("0"),
        )
        assert result == Decimal("0")


class TestPKPCalculation:
    """Tests for PKP (Penghasilan Kena Pajak / Taxable Income) calculation."""

    def test_pkp_standard_case(self):
        """Standard PKP calculation with all deductions.

        Annual gross 240,000,000
        - Biaya jabatan 6,000,000
        - BPJS deductible 3,600,000
        - PTKP 54,000,000 (TK/0)
        = PKP 176,400,000
        """
        result = calculate_pkp(
            annual_gross=Decimal("240000000"),
            biaya_jabatan=Decimal("6000000"),
            annual_bpjs_deductible=Decimal("3600000"),
            ptkp_annual=Decimal("54000000"),
        )
        assert result == Decimal("176400000")

    def test_pkp_negative_returns_zero(self):
        """When deductions exceed gross, PKP should be 0 (not negative).

        Annual gross 48,000,000 (monthly 4M)
        - Biaya jabatan 2,400,000
        - BPJS deductible 1,200,000
        - PTKP 54,000,000 (TK/0)
        = -9,600,000 → clipped to 0
        """
        result = calculate_pkp(
            annual_gross=Decimal("48000000"),
            biaya_jabatan=Decimal("2400000"),
            annual_bpjs_deductible=Decimal("1200000"),
            ptkp_annual=Decimal("54000000"),
        )
        assert result == Decimal("0")

    def test_pkp_exactly_zero(self):
        """PKP exactly at zero boundary."""
        result = calculate_pkp(
            annual_gross=Decimal("60000000"),
            biaya_jabatan=Decimal("3000000"),
            annual_bpjs_deductible=Decimal("3000000"),
            ptkp_annual=Decimal("54000000"),
        )
        assert result == Decimal("0")


class TestProgressiveBrackets:
    """Tests for applying Pasal 17 progressive tax brackets."""

    def test_brackets_two_brackets(self, pasal17_brackets):
        """PKP 176,400,000 spans first two brackets.

        First 60M × 5% = 3,000,000
        Next 116,400,000 × 15% = 17,460,000
        Total = 20,460,000
        """
        pkp = Decimal("176400000")
        result = apply_progressive_brackets(pkp, pasal17_brackets)
        assert result == Decimal("20460000")

    def test_brackets_exactly_one_bracket(self, pasal17_brackets):
        """PKP exactly 60,000,000 → all in first bracket.

        60M × 5% = 3,000,000
        """
        pkp = Decimal("60000000")
        result = apply_progressive_brackets(pkp, pasal17_brackets)
        assert result == Decimal("3000000")

    def test_brackets_zero_pkp(self, pasal17_brackets):
        """PKP = 0 → tax = 0."""
        result = apply_progressive_brackets(Decimal("0"), pasal17_brackets)
        assert result == Decimal("0")

    def test_brackets_negative_pkp(self, pasal17_brackets):
        """Negative PKP → tax = 0."""
        result = apply_progressive_brackets(Decimal("-1000000"), pasal17_brackets)
        assert result == Decimal("0")

    def test_brackets_small_pkp(self, pasal17_brackets):
        """PKP 10,000,000 → all in first bracket (5%).

        10M × 5% = 500,000
        """
        pkp = Decimal("10000000")
        result = apply_progressive_brackets(pkp, pasal17_brackets)
        assert result == Decimal("500000")

    def test_brackets_three_brackets(self, pasal17_brackets):
        """PKP 300,000,000 spans three brackets.

        First 60M × 5% = 3,000,000
        Next 190M × 15% = 28,500,000
        Next 50M × 25% = 12,500,000
        Total = 44,000,000
        """
        pkp = Decimal("300000000")
        result = apply_progressive_brackets(pkp, pasal17_brackets)
        assert result == Decimal("44000000")


class TestMonthlyPPh21Pasal17:
    """Tests for full monthly PPh 21 calculation using Pasal 17 method."""

    def test_full_monthly_calculation(self, pasal17_brackets, ptkp_tk0):
        """Full monthly PPh 21 calculation for a standard employee.

        Monthly gross: 20,000,000
        BPJS JHT emp: 200,000 (2% of 10M base)
        BPJS JP emp: 100,000 (1% of 10M, capped)
        PTKP: TK/0 = 54,000,000

        Steps:
        1. Annual gross = 20M × 12 = 240,000,000
        2. Biaya jabatan = min(5% × 240M, 6M) = 6,000,000
        3. Annual BPJS = (200K + 100K) × 12 = 3,600,000
        4. PKP = 240M - 6M - 3.6M - 54M = 176,400,000
        5. Tax: 60M×5% + 116.4M×15% = 3M + 17.46M = 20,460,000
        6. Monthly = 20,460,000 / 12 = 1,705,000
        """
        result = calculate_monthly_pph21_pasal17(
            monthly_gross=Decimal("20000000"),
            monthly_bpjs_jht_employee=Decimal("200000"),
            monthly_bpjs_jp_employee=Decimal("100000"),
            ptkp_annual=ptkp_tk0,
            brackets=pasal17_brackets,
        )
        assert result == Decimal("1705000")

    def test_zero_tax_low_income(self, pasal17_brackets, ptkp_tk0):
        """Monthly gross 4,000,000 with TK/0 → PKP negative → tax = 0.

        Annual gross = 48,000,000
        Biaya jabatan = 2,400,000
        BPJS = 0 (assume no BPJS for this test)
        PKP = 48M - 2.4M - 0 - 54M = -8,400,000 → 0
        Tax = 0
        """
        result = calculate_monthly_pph21_pasal17(
            monthly_gross=Decimal("4000000"),
            monthly_bpjs_jht_employee=Decimal("0"),
            monthly_bpjs_jp_employee=Decimal("0"),
            ptkp_annual=ptkp_tk0,
            brackets=pasal17_brackets,
        )
        assert result == Decimal("0")

    def test_boundary_pkp_exactly_one_bracket(self, pasal17_brackets):
        """PKP exactly at bracket boundary (60M) → tax = 3,000,000 annual.

        We need monthly_gross such that PKP = 60,000,000.
        PKP = annual_gross - biaya_jabatan - bpjs - ptkp
        Let BPJS = 0, PTKP = 54M.
        annual_gross - min(5% × annual_gross, 6M) - 54M = 60M
        If annual_gross > 120M: annual_gross - 6M - 54M = 60M → annual_gross = 120M
        monthly_gross = 10,000,000
        Verify: annual=120M, biaya=6M, PKP=120-6-0-54=60M ✓
        Tax = 3,000,000/year, monthly = 250,000
        """
        result = calculate_monthly_pph21_pasal17(
            monthly_gross=Decimal("10000000"),
            monthly_bpjs_jht_employee=Decimal("0"),
            monthly_bpjs_jp_employee=Decimal("0"),
            ptkp_annual=Decimal("54000000"),
            brackets=pasal17_brackets,
        )
        assert result == Decimal("250000")
