"""
PPh 21 calculation using TER (Tarif Efektif Rata-rata) per PMK 168/2023.
All functions are PURE — no DB access, no side effects.

Monthly: tax = monthly_gross x TER_rate
December: Recalculate full year with Pasal 17, subtract Jan-Nov TER taxes

TER categories are determined by PTKP status:
- Category A: TK/0, TK/1
- Category B: TK/2, TK/3, K/0, K/1
- Category C: K/2, K/3
"""
from decimal import Decimal
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TerBracketData:
    """In-memory TER bracket."""

    category: str  # A, B, or C
    income_range_min: Decimal
    income_range_max: Decimal
    ter_rate: Decimal


# PTKP status to TER category mapping per PMK 168/2023
PTKP_TO_TER_CATEGORY = {
    "TK/0": "A",
    "TK/1": "A",
    "TK/2": "B",
    "TK/3": "B",
    "K/0": "B",
    "K/1": "B",
    "K/2": "C",
    "K/3": "C",
}


def get_ter_category(ptkp_status: str) -> str:
    """Map PTKP status code to TER category (A/B/C).

    Per PMK 168/2023:
    - Category A: TK/0, TK/1
    - Category B: TK/2, TK/3, K/0, K/1
    - Category C: K/2, K/3

    Args:
        ptkp_status: PTKP status code (e.g., "TK/0", "K/1")

    Returns:
        TER category letter ("A", "B", or "C")

    Raises:
        TaxCalculationError: If PTKP status is unknown
    """
    category = PTKP_TO_TER_CATEGORY.get(ptkp_status)
    if category is None:
        from app.exceptions import TaxCalculationError

        raise TaxCalculationError(f"Unknown PTKP status: {ptkp_status}")
    return category


def find_ter_rate(
    monthly_gross: Decimal, category: str, ter_brackets: List[TerBracketData]
) -> Decimal:
    """Find the TER rate for given income and category using sorted bracket lookup.

    Args:
        monthly_gross: Monthly gross income
        category: TER category (A, B, or C)
        ter_brackets: List of all TER bracket data

    Returns:
        The applicable TER rate as Decimal (e.g., Decimal("0.0025") for 0.25%)

    Raises:
        TaxCalculationError: If no bracket is found for the category
    """
    # Filter brackets for the category and sort by income_range_min
    category_brackets = sorted(
        [b for b in ter_brackets if b.category == category],
        key=lambda b: b.income_range_min,
    )

    for bracket in category_brackets:
        if bracket.income_range_min <= monthly_gross <= bracket.income_range_max:
            return bracket.ter_rate

    # If income exceeds all brackets, use the highest bracket's rate
    if category_brackets:
        return category_brackets[-1].ter_rate

    from app.exceptions import TaxCalculationError

    raise TaxCalculationError(
        f"No TER bracket found for category={category}, income={monthly_gross}"
    )


def calculate_monthly_pph21_ter(monthly_gross: Decimal, ter_rate: Decimal) -> Decimal:
    """Calculate monthly PPh 21 using TER method: gross x rate.

    Per PMK 168/2023: For months January through November,
    PPh 21 = Penghasilan Bruto x TER rate.

    Args:
        monthly_gross: Monthly gross income
        ter_rate: Applicable TER rate

    Returns:
        Monthly PPh 21 tax amount (rounded to nearest Rupiah)
    """
    from app.utils.decimal_utils import round_money

    return round_money(monthly_gross * ter_rate)


def calculate_december_reconciliation(
    annual_gross: Decimal,
    ptkp_annual: Decimal,
    monthly_bpjs_jht_employee: Decimal,
    monthly_bpjs_jp_employee: Decimal,
    brackets,  # List[TaxBracket] from pph21_pasal17
    ter_taxes_jan_to_nov: Decimal,
) -> Decimal:
    """December year-end reconciliation for TER method.

    Per PMK 168/2023: In December (or final month of employment),
    the actual annual tax is recalculated using Pasal 17 progressive method.
    December tax = Full year Pasal 17 tax - sum of Jan-Nov TER taxes paid.

    Steps:
    1. Calculate full-year tax using Pasal 17 progressive method
    2. December tax = Annual Pasal 17 tax - Sum(Jan-Nov TER taxes)
    3. If result is negative (overpaid), return 0

    Args:
        annual_gross: Total gross income for the full year (Jan-Dec)
        ptkp_annual: Annual PTKP amount
        monthly_bpjs_jht_employee: Monthly BPJS JHT employee contribution
        monthly_bpjs_jp_employee: Monthly BPJS JP employee contribution
        brackets: List of TaxBracket for Pasal 17 progressive calculation
        ter_taxes_jan_to_nov: Sum of PPh 21 taxes paid via TER from Jan to Nov

    Returns:
        December PPh 21 tax amount (rounded to nearest Rupiah, non-negative)
    """
    from app.calculations.pph21_pasal17 import (
        calculate_biaya_jabatan,
        calculate_annual_bpjs_deductible,
        calculate_pkp,
        apply_progressive_brackets,
    )
    from app.utils.decimal_utils import round_money, ensure_non_negative

    biaya_jabatan = calculate_biaya_jabatan(annual_gross)
    annual_bpjs = calculate_annual_bpjs_deductible(
        monthly_bpjs_jht_employee, monthly_bpjs_jp_employee
    )
    pkp = calculate_pkp(annual_gross, biaya_jabatan, annual_bpjs, ptkp_annual)
    annual_tax_pasal17 = apply_progressive_brackets(pkp, brackets)

    december_tax = annual_tax_pasal17 - ter_taxes_jan_to_nov
    return round_money(ensure_non_negative(december_tax))
