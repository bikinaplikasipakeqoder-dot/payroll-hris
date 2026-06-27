"""Unit tests for PPh 21 TER (Tarif Efektif Rata-rata) method per PMK 168/2023."""
import pytest
from decimal import Decimal

from app.calculations.pph21_ter import (
    get_ter_category,
    find_ter_rate,
    calculate_monthly_pph21_ter,
    calculate_december_reconciliation,
    PTKP_TO_TER_CATEGORY,
)
from app.exceptions import TaxCalculationError


class TestPTKPToCategoryMapping:
    """Tests for PTKP status to TER category mapping."""

    def test_tk0_maps_to_category_a(self):
        """TK/0 (single, no dependents) → Category A."""
        assert get_ter_category("TK/0") == "A"

    def test_tk1_maps_to_category_a(self):
        """TK/1 (single, 1 dependent) → Category A."""
        assert get_ter_category("TK/1") == "A"

    def test_k0_maps_to_category_b(self):
        """K/0 (married, no dependents) → Category B."""
        assert get_ter_category("K/0") == "B"

    def test_k1_maps_to_category_b(self):
        """K/1 (married, 1 dependent) → Category B."""
        assert get_ter_category("K/1") == "B"

    def test_tk2_maps_to_category_b(self):
        """TK/2 (single, 2 dependents) → Category B."""
        assert get_ter_category("TK/2") == "B"

    def test_tk3_maps_to_category_b(self):
        """TK/3 (single, 3 dependents) → Category B."""
        assert get_ter_category("TK/3") == "B"

    def test_k2_maps_to_category_c(self):
        """K/2 (married, 2 dependents) → Category C."""
        assert get_ter_category("K/2") == "C"

    def test_k3_maps_to_category_c(self):
        """K/3 (married, 3 dependents) → Category C."""
        assert get_ter_category("K/3") == "C"

    def test_unknown_status_raises_error(self):
        """Unknown PTKP status should raise TaxCalculationError."""
        with pytest.raises(TaxCalculationError):
            get_ter_category("INVALID")


class TestTERRateLookup:
    """Tests for TER rate lookup from brackets."""

    def test_category_a_income_10m(self, sample_ter_brackets):
        """Category A, income 10,000,000 → rate from bracket 9,650,001 - 10,050,000 = 0.02."""
        rate = find_ter_rate(Decimal("10000000"), "A", sample_ter_brackets)
        assert rate == Decimal("0.02")

    def test_category_b_income_15m(self, sample_ter_brackets):
        """Category B, income 15,000,000 → rate from bracket 13,750,001 - 15,100,000 = 0.04."""
        rate = find_ter_rate(Decimal("15000000"), "B", sample_ter_brackets)
        assert rate == Decimal("0.04")

    def test_category_a_zero_income(self, sample_ter_brackets):
        """Category A, income 0 → rate = 0 (first bracket)."""
        rate = find_ter_rate(Decimal("0"), "A", sample_ter_brackets)
        assert rate == Decimal("0")

    def test_category_c_income_8m(self, sample_ter_brackets):
        """Category C, income 8,000,000 → rate from bracket 7,800,001 - 8,850,000 = 0.01."""
        rate = find_ter_rate(Decimal("8000000"), "C", sample_ter_brackets)
        assert rate == Decimal("0.01")

    def test_income_exceeds_all_brackets_uses_highest(self, sample_ter_brackets):
        """Income exceeding all brackets should use the highest bracket's rate."""
        rate = find_ter_rate(Decimal("50000000"), "A", sample_ter_brackets)
        # Should return the last bracket's rate for category A
        assert rate == Decimal("0.035")

    def test_empty_category_raises_error(self):
        """No brackets for category should raise TaxCalculationError."""
        with pytest.raises(TaxCalculationError):
            find_ter_rate(Decimal("10000000"), "X", [])


class TestMonthlyTERCalculation:
    """Tests for monthly PPh 21 TER method: gross × rate."""

    def test_monthly_ter_standard(self):
        """Monthly gross 10,000,000, TER rate 2.5% → tax = 250,000."""
        result = calculate_monthly_pph21_ter(
            monthly_gross=Decimal("10000000"),
            ter_rate=Decimal("0.025"),
        )
        assert result == Decimal("250000")

    def test_monthly_ter_zero_rate(self):
        """Zero TER rate → tax = 0."""
        result = calculate_monthly_pph21_ter(
            monthly_gross=Decimal("10000000"),
            ter_rate=Decimal("0"),
        )
        assert result == Decimal("0")

    def test_monthly_ter_small_rate(self):
        """Monthly gross 8,000,000, TER rate 0.25% → tax = 20,000."""
        result = calculate_monthly_pph21_ter(
            monthly_gross=Decimal("8000000"),
            ter_rate=Decimal("0.0025"),
        )
        assert result == Decimal("20000")

    def test_monthly_ter_higher_income(self):
        """Monthly gross 15,000,000, TER rate 4% → tax = 600,000."""
        result = calculate_monthly_pph21_ter(
            monthly_gross=Decimal("15000000"),
            ter_rate=Decimal("0.04"),
        )
        assert result == Decimal("600000")


class TestDecemberReconciliation:
    """Tests for December year-end reconciliation (TER → Pasal 17)."""

    def test_december_reconciliation_standard(self, pasal17_brackets):
        """December reconciliation with consistent monthly income.

        Scenario: Employee with monthly gross 10,000,000, TK/0
        Annual gross = 120,000,000
        BPJS JHT emp = 0, JP emp = 0 (simplified)
        PTKP = 54,000,000

        Pasal 17 full-year calculation:
        - Biaya jabatan = min(5% × 120M, 6M) = 6,000,000
        - BPJS annual = 0
        - PKP = 120M - 6M - 0 - 54M = 60,000,000
        - Tax = 60M × 5% = 3,000,000

        If Jan-Nov TER taxes = 11 × 250,000 = 2,750,000
        December tax = 3,000,000 - 2,750,000 = 250,000
        """
        result = calculate_december_reconciliation(
            annual_gross=Decimal("120000000"),
            ptkp_annual=Decimal("54000000"),
            monthly_bpjs_jht_employee=Decimal("0"),
            monthly_bpjs_jp_employee=Decimal("0"),
            brackets=pasal17_brackets,
            ter_taxes_jan_to_nov=Decimal("2750000"),
        )
        assert result == Decimal("250000")

    def test_december_reconciliation_overpaid_returns_zero(self, pasal17_brackets):
        """If TER overpaid through the year, December tax = 0 (non-negative).

        Annual Pasal 17 tax = 3,000,000 but Jan-Nov TER = 3,500,000
        December = max(0, 3M - 3.5M) = 0
        """
        result = calculate_december_reconciliation(
            annual_gross=Decimal("120000000"),
            ptkp_annual=Decimal("54000000"),
            monthly_bpjs_jht_employee=Decimal("0"),
            monthly_bpjs_jp_employee=Decimal("0"),
            brackets=pasal17_brackets,
            ter_taxes_jan_to_nov=Decimal("3500000"),
        )
        assert result == Decimal("0")

    def test_december_reconciliation_with_bpjs(self, pasal17_brackets):
        """December reconciliation with BPJS deductions included.

        Annual gross = 240,000,000 (monthly 20M)
        BPJS JHT emp = 200,000/month, JP emp = 100,000/month
        PTKP = 54,000,000

        Pasal 17:
        - Biaya jabatan = 6,000,000
        - Annual BPJS = 3,600,000
        - PKP = 240M - 6M - 3.6M - 54M = 176,400,000
        - Tax: 60M×5% + 116.4M×15% = 3M + 17.46M = 20,460,000

        If Jan-Nov TER taxes paid = 18,755,000
        December tax = 20,460,000 - 18,755,000 = 1,705,000
        """
        result = calculate_december_reconciliation(
            annual_gross=Decimal("240000000"),
            ptkp_annual=Decimal("54000000"),
            monthly_bpjs_jht_employee=Decimal("200000"),
            monthly_bpjs_jp_employee=Decimal("100000"),
            brackets=pasal17_brackets,
            ter_taxes_jan_to_nov=Decimal("18755000"),
        )
        assert result == Decimal("1705000")
