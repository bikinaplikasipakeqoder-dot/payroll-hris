"""Unit tests for Gross/Nett payroll method calculation."""
import pytest
from decimal import Decimal

from app.calculations.gross_nett import (
    calculate_gross_method,
    calculate_nett_method_grossup,
    MAX_ITERATIONS,
    CONVERGENCE_TOLERANCE,
)
from app.calculations.pph21_pasal17 import (
    TaxBracket,
    calculate_monthly_pph21_pasal17,
)
from app.exceptions import TaxCalculationError


class TestGrossMethod:
    """Tests for GROSS payroll method (employee bears tax)."""

    def test_gross_method_standard(self):
        """Standard gross method deduction.

        Gross 20,000,000
        - Tax 1,500,000
        - BPJS emp 500,000
        - Kasbon 1,000,000
        - Other 0
        = Net 17,000,000
        """
        result = calculate_gross_method(
            gross_salary=Decimal("20000000"),
            pph21_tax=Decimal("1500000"),
            bpjs_employee_total=Decimal("500000"),
            kasbon_deduction=Decimal("1000000"),
            other_deductions=Decimal("0"),
        )
        assert result == Decimal("17000000")

    def test_gross_method_all_deductions(self):
        """Gross method with all types of deductions.

        Gross 15,000,000
        - Tax 800,000
        - BPJS 400,000
        - Kasbon 500,000
        - Other 200,000
        = Net 13,100,000
        """
        result = calculate_gross_method(
            gross_salary=Decimal("15000000"),
            pph21_tax=Decimal("800000"),
            bpjs_employee_total=Decimal("400000"),
            kasbon_deduction=Decimal("500000"),
            other_deductions=Decimal("200000"),
        )
        assert result == Decimal("13100000")

    def test_gross_method_no_deductions(self):
        """No deductions → net = gross."""
        result = calculate_gross_method(
            gross_salary=Decimal("10000000"),
            pph21_tax=Decimal("0"),
            bpjs_employee_total=Decimal("0"),
            kasbon_deduction=Decimal("0"),
            other_deductions=Decimal("0"),
        )
        assert result == Decimal("10000000")

    def test_gross_method_deductions_exceed_gross_returns_zero(self):
        """When deductions exceed gross, net should be 0 (non-negative).

        Gross 5,000,000 - Tax 3M - BPJS 2M - Kasbon 2M = -2M → 0
        """
        result = calculate_gross_method(
            gross_salary=Decimal("5000000"),
            pph21_tax=Decimal("3000000"),
            bpjs_employee_total=Decimal("2000000"),
            kasbon_deduction=Decimal("2000000"),
            other_deductions=Decimal("0"),
        )
        assert result == Decimal("0")


class TestNettMethodGrossUp:
    """Tests for NETT method (iterative gross-up / tax allowance)."""

    def test_nett_grossup_flat_rate_converges(self):
        """Nett gross-up with simple 10% flat tax rate converges.

        Base gross: 10,000,000
        Tax function: 10% flat rate (rounded to Rupiah)
        Expected: tax_allowance ≈ 1,111,111 (10M × 0.1 / (1-0.1))
        """
        from app.utils.decimal_utils import round_money

        def flat_tax_10_percent(gross: Decimal) -> Decimal:
            return round_money(gross * Decimal("0.1"))

        tax_allowance, final_tax = calculate_nett_method_grossup(
            base_gross=Decimal("10000000"),
            tax_calculator_fn=flat_tax_10_percent,
        )

        # Tax allowance should be approximately 1,111,111
        assert abs(tax_allowance - Decimal("1111111")) <= Decimal("1")
        # Final tax should equal tax_allowance (since company covers it)
        assert final_tax == tax_allowance

    def test_nett_grossup_zero_tax(self):
        """When tax function returns 0, no gross-up needed.

        Base gross: 4,000,000 (below PTKP threshold, so tax = 0)
        """

        def zero_tax(gross: Decimal) -> Decimal:
            return Decimal("0")

        tax_allowance, final_tax = calculate_nett_method_grossup(
            base_gross=Decimal("4000000"),
            tax_calculator_fn=zero_tax,
        )

        assert tax_allowance == Decimal("0")
        assert final_tax == Decimal("0")

    def test_nett_grossup_with_progressive_brackets(self, pasal17_brackets):
        """Nett gross-up with real Pasal 17 brackets converges.

        Base gross: 15,000,000/month
        Using full Pasal 17 calculation (annualize, biaya jabatan, PKP, brackets)
        PTKP: 54,000,000, no BPJS (simplified)

        After gross-up:
        - Employee receives full base_gross as net
        - Company provides tax_allowance as additional benefit
        """

        def pasal17_tax_fn(monthly_gross: Decimal) -> Decimal:
            return calculate_monthly_pph21_pasal17(
                monthly_gross=monthly_gross,
                monthly_bpjs_jht_employee=Decimal("0"),
                monthly_bpjs_jp_employee=Decimal("0"),
                ptkp_annual=Decimal("54000000"),
                brackets=pasal17_brackets,
            )

        tax_allowance, final_tax = calculate_nett_method_grossup(
            base_gross=Decimal("15000000"),
            tax_calculator_fn=pasal17_tax_fn,
        )

        # Must converge (no exception raised)
        assert tax_allowance > Decimal("0")
        assert final_tax > Decimal("0")
        # Tax allowance and final tax should be equal (company covers the tax)
        assert tax_allowance == final_tax
        # Verify: tax on (base_gross + tax_allowance) = final_tax
        verification_tax = pasal17_tax_fn(Decimal("15000000") + tax_allowance)
        assert abs(verification_tax - final_tax) <= Decimal("1")

    def test_nett_grossup_convergence_iterations(self):
        """Verify gross-up converges within reasonable iterations.

        Using a 5% flat rate for faster convergence.
        Mathematical: allowance = base × rate / (1 - rate) = 10M × 0.05/0.95 ≈ 526,316
        """
        from app.utils.decimal_utils import round_money

        def flat_tax_5_percent(gross: Decimal) -> Decimal:
            return round_money(gross * Decimal("0.05"))

        tax_allowance, final_tax = calculate_nett_method_grossup(
            base_gross=Decimal("10000000"),
            tax_calculator_fn=flat_tax_5_percent,
        )

        expected_allowance = Decimal("526316")  # 10M × 0.05 / 0.95 ≈ 526,315.78 → 526,316
        assert abs(tax_allowance - expected_allowance) <= Decimal("1")

    def test_nett_grossup_custom_tolerance(self):
        """Gross-up with custom tolerance."""
        from app.utils.decimal_utils import round_money

        def flat_tax_10_percent(gross: Decimal) -> Decimal:
            return round_money(gross * Decimal("0.1"))

        tax_allowance, final_tax = calculate_nett_method_grossup(
            base_gross=Decimal("10000000"),
            tax_calculator_fn=flat_tax_10_percent,
            tolerance=Decimal("100"),
        )

        # Should still converge but potentially in fewer iterations
        assert abs(tax_allowance - Decimal("1111111")) <= Decimal("100")
