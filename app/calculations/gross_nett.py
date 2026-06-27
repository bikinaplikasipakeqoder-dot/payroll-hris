"""
Gross vs Nett payroll method calculation.
All functions are PURE — no DB access, no side effects.

GROSS method:
  Net = Gross - PPh21 - BPJS Employee - Kasbon - Other Deductions
  Employee bears the tax.

NETT method (Tax Allowance / Gross-Up):
  Company pays the tax on behalf of employee.
  Tax becomes "Tunjangan Pajak" (tax allowance) added to gross.
  Requires iterative calculation because tax on the tax allowance
  also needs to be covered.

  Iteration:
  1. Start: tax_allowance = 0
  2. new_gross = base_gross + tax_allowance
  3. tax = calculate_tax(new_gross)
  4. new_tax_allowance = tax
  5. If |new_tax_allowance - tax_allowance| < tolerance: converged
  6. Else: tax_allowance = new_tax_allowance, repeat from step 2

  Typically converges in 3-5 iterations. Max 10 iterations as safety.
"""
from decimal import Decimal
from typing import Callable, Tuple
import logging

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 10
CONVERGENCE_TOLERANCE = Decimal("1")  # 1 IDR


def calculate_gross_method(
    gross_salary: Decimal,
    pph21_tax: Decimal,
    bpjs_employee_total: Decimal,
    kasbon_deduction: Decimal,
    other_deductions: Decimal,
) -> Decimal:
    """Calculate net salary using GROSS method.

    Net = Gross - Tax - BPJS Employee - Kasbon - Other Deductions

    In GROSS method, the employee bears the full income tax.
    All deductions are subtracted from gross to arrive at take-home pay.

    Args:
        gross_salary: Total gross salary (base + allowances + OT + bonus)
        pph21_tax: PPh 21 income tax amount
        bpjs_employee_total: Total employee BPJS contributions (KES + JHT + JP)
        kasbon_deduction: Salary advance (kasbon) installment deduction
        other_deductions: Any other deductions (late penalties, etc.)

    Returns:
        Net take-home pay (rounded to nearest Rupiah, non-negative)
    """
    from app.utils.decimal_utils import round_money, ensure_non_negative

    net = (
        gross_salary
        - pph21_tax
        - bpjs_employee_total
        - kasbon_deduction
        - other_deductions
    )
    return round_money(ensure_non_negative(net))


def calculate_nett_method_grossup(
    base_gross: Decimal,
    tax_calculator_fn: Callable[[Decimal], Decimal],
    max_iterations: int = MAX_ITERATIONS,
    tolerance: Decimal = CONVERGENCE_TOLERANCE,
) -> Tuple[Decimal, Decimal]:
    """Calculate tax allowance using Nett method (iterative gross-up).

    In the NETT method, the company bears the employee's tax burden.
    The tax is added as "Tunjangan Pajak" (tax allowance) to the gross.
    Since this increases gross income, it also increases the tax,
    requiring iterative convergence.

    Args:
        base_gross: Gross salary before tax allowance (base + allowances + OT + bonus)
        tax_calculator_fn: Function that takes gross and returns PPh21 tax amount.
                          Must be a pure function accepting Decimal and returning Decimal.
        max_iterations: Safety cap on iterations (default 10)
        tolerance: Convergence tolerance in IDR (default 1 IDR)

    Returns:
        Tuple of (tax_allowance, final_tax):
        - tax_allowance: Amount company pays as tax benefit to employee
        - final_tax: The actual PPh21 amount calculated on the full gross

    Raises:
        TaxCalculationError: If calculation fails to converge after max_iterations
    """
    from app.utils.decimal_utils import round_money
    from app.exceptions import TaxCalculationError

    tax_allowance = Decimal("0")

    for iteration in range(1, max_iterations + 1):
        grossed_up = base_gross + tax_allowance
        new_tax = tax_calculator_fn(grossed_up)
        new_tax_allowance = new_tax

        delta = abs(new_tax_allowance - tax_allowance)

        if delta <= tolerance:
            logger.debug(f"Nett gross-up converged in {iteration} iterations")
            return round_money(new_tax_allowance), round_money(new_tax)

        tax_allowance = new_tax_allowance

    # If we hit max iterations, log warning and use last calculated value
    logger.warning(
        f"Nett gross-up did not converge after {max_iterations} iterations. "
        f"Last delta: {delta} IDR. Using last calculated value."
    )
    final_tax_allowance = round_money(tax_allowance)
    final_tax = round_money(tax_calculator_fn(base_gross + tax_allowance))
    return final_tax_allowance, final_tax
