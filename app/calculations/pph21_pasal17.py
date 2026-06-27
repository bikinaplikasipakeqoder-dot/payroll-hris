"""
PPh 21 calculation using Pasal 17 progressive tax brackets (UU HPP).
All functions are PURE — no DB access, no side effects.

Formula:
1. Annual Gross = Monthly Gross × 12
2. Biaya Jabatan = min(5% × Annual Gross, 6,000,000)
3. BPJS deductible = (JHT employee + JP employee) × 12
4. PKP = Annual Gross - Biaya Jabatan - BPJS deductible - PTKP
5. If PKP <= 0: tax = 0
6. Apply progressive brackets to PKP
7. Monthly tax = Annual tax / 12
"""
from decimal import Decimal
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class TaxBracket:
    """In-memory representation of a tax bracket."""

    lower_bound: Decimal  # income_range_min
    upper_bound: Optional[Decimal]  # income_range_max (None for last bracket)
    rate: Decimal  # e.g., Decimal("0.05") for 5%


BIAYA_JABATAN_RATE = Decimal("0.05")
BIAYA_JABATAN_MAX_ANNUAL = Decimal("6000000")
BIAYA_JABATAN_MAX_MONTHLY = Decimal("500000")


def calculate_biaya_jabatan(annual_gross: Decimal) -> Decimal:
    """5% of annual gross income, max 6,000,000/year.

    Per PP 68/2009: Biaya Jabatan = 5% × Penghasilan Bruto,
    maximum Rp 6.000.000/tahun or Rp 500.000/bulan.
    """
    return min(annual_gross * BIAYA_JABATAN_RATE, BIAYA_JABATAN_MAX_ANNUAL)


def calculate_annual_bpjs_deductible(
    monthly_jht_employee: Decimal, monthly_jp_employee: Decimal
) -> Decimal:
    """Annual BPJS JHT + JP employee contribution (deductible from tax base).

    Per PMK 250/PMK.03/2008: Employee BPJS JHT and JP contributions
    are deductible from gross income for PPh 21 calculation.
    """
    return (monthly_jht_employee + monthly_jp_employee) * Decimal("12")


def calculate_pkp(
    annual_gross: Decimal,
    biaya_jabatan: Decimal,
    annual_bpjs_deductible: Decimal,
    ptkp_annual: Decimal,
) -> Decimal:
    """Calculate PKP (Penghasilan Kena Pajak / Taxable Income).

    PKP = Annual Gross - Biaya Jabatan - BPJS Deductible - PTKP
    Returns 0 if result is negative (no negative taxable income).
    """
    pkp = annual_gross - biaya_jabatan - annual_bpjs_deductible - ptkp_annual
    return max(pkp, Decimal("0"))


def apply_progressive_brackets(pkp: Decimal, brackets: List[TaxBracket]) -> Decimal:
    """Apply Pasal 17 progressive tax brackets to PKP.

    Brackets (UU HPP 2022 / UU 7/2021):
    - 0 - 60,000,000: 5%
    - >60,000,000 - 250,000,000: 15%
    - >250,000,000 - 500,000,000: 25%
    - >500,000,000 - 5,000,000,000: 30%
    - >5,000,000,000: 35%

    Each bracket's taxable portion = min(remaining_pkp, bracket_width) × rate
    """
    if pkp <= Decimal("0"):
        return Decimal("0")

    total_tax = Decimal("0")
    remaining = pkp

    for bracket in sorted(brackets, key=lambda b: b.lower_bound):
        if remaining <= Decimal("0"):
            break
        if bracket.upper_bound is None:
            # Last bracket — no upper limit
            taxable_in_bracket = remaining
        else:
            bracket_width = bracket.upper_bound - bracket.lower_bound
            taxable_in_bracket = min(remaining, bracket_width)
        total_tax += taxable_in_bracket * bracket.rate
        remaining -= taxable_in_bracket

    return total_tax


def calculate_monthly_pph21_pasal17(
    monthly_gross: Decimal,
    monthly_bpjs_jht_employee: Decimal,
    monthly_bpjs_jp_employee: Decimal,
    ptkp_annual: Decimal,
    brackets: List[TaxBracket],
) -> Decimal:
    """Calculate monthly PPh 21 using Pasal 17 method.

    Steps:
    1. Annualize gross income
    2. Calculate biaya jabatan
    3. Calculate annual BPJS deductible
    4. Calculate PKP
    5. Apply progressive brackets
    6. Divide by 12 for monthly amount

    Args:
        monthly_gross: Total monthly gross income (salary + taxable allowances + OT + bonus)
        monthly_bpjs_jht_employee: Monthly BPJS JHT employee contribution
        monthly_bpjs_jp_employee: Monthly BPJS JP employee contribution
        ptkp_annual: Annual PTKP amount based on employee's status (TK/0, K/1, etc.)
        brackets: List of progressive tax brackets

    Returns:
        Monthly PPh 21 tax amount (rounded to nearest Rupiah)
    """
    annual_gross = monthly_gross * Decimal("12")
    biaya_jabatan = calculate_biaya_jabatan(annual_gross)
    annual_bpjs = calculate_annual_bpjs_deductible(
        monthly_bpjs_jht_employee, monthly_bpjs_jp_employee
    )
    pkp = calculate_pkp(annual_gross, biaya_jabatan, annual_bpjs, ptkp_annual)
    annual_tax = apply_progressive_brackets(pkp, brackets)
    monthly_tax = annual_tax / Decimal("12")

    from app.utils.decimal_utils import round_money

    return round_money(monthly_tax)
"""
PPh 21 calculation using Pasal 17 progressive tax brackets (UU HPP).
All functions are PURE — no DB access, no side effects.

Formula:
1. Annual Gross = Monthly Gross × 12
2. Biaya Jabatan = min(5% × Annual Gross, 6,000,000)
3. BPJS deductible = (JHT employee + JP employee) × 12
4. PKP = Annual Gross - Biaya Jabatan - BPJS deductible - PTKP
5. If PKP <= 0: tax = 0
6. Apply progressive brackets to PKP
7. Monthly tax = Annual tax / 12
"""
from decimal import Decimal
from typing import List
from dataclasses import dataclass


@dataclass
class TaxBracket:
    """In-memory representation of a tax bracket."""

    lower_bound: Decimal  # income_range_min
    upper_bound: Decimal  # income_range_max (use very large number for last bracket)
    rate: Decimal  # e.g., Decimal("0.05") for 5%


BIAYA_JABATAN_RATE = Decimal("0.05")
BIAYA_JABATAN_MAX_ANNUAL = Decimal("6000000")
BIAYA_JABATAN_MAX_MONTHLY = Decimal("500000")


def calculate_biaya_jabatan(annual_gross: Decimal) -> Decimal:
    """5% of annual gross income, max 6,000,000/year.

    Per PP 68/2009: Biaya Jabatan = 5% x Penghasilan Bruto,
    maximum Rp 6.000.000/tahun or Rp 500.000/bulan.
    """
    return min(annual_gross * BIAYA_JABATAN_RATE, BIAYA_JABATAN_MAX_ANNUAL)


def calculate_annual_bpjs_deductible(
    monthly_jht_employee: Decimal, monthly_jp_employee: Decimal
) -> Decimal:
    """Annual BPJS JHT + JP employee contribution (deductible from tax base).

    Per PMK 250/PMK.03/2008: Employee BPJS JHT and JP contributions
    are deductible from gross income for PPh 21 calculation.
    """
    return (monthly_jht_employee + monthly_jp_employee) * Decimal("12")


def calculate_pkp(
    annual_gross: Decimal,
    biaya_jabatan: Decimal,
    annual_bpjs_deductible: Decimal,
    ptkp_annual: Decimal,
) -> Decimal:
    """Calculate PKP (Penghasilan Kena Pajak / Taxable Income).

    PKP = Annual Gross - Biaya Jabatan - BPJS Deductible - PTKP
    Returns 0 if result is negative (no negative taxable income).
    """
    pkp = annual_gross - biaya_jabatan - annual_bpjs_deductible - ptkp_annual
    return max(pkp, Decimal("0"))


def apply_progressive_brackets(pkp: Decimal, brackets: List[TaxBracket]) -> Decimal:
    """Apply Pasal 17 progressive tax brackets to PKP.

    Brackets (UU HPP 2022 / UU 7/2021):
    - 0 - 60,000,000: 5%
    - >60,000,000 - 250,000,000: 15%
    - >250,000,000 - 500,000,000: 25%
    - >500,000,000 - 5,000,000,000: 30%
    - >5,000,000,000: 35%

    Each bracket's taxable portion = min(remaining_pkp, bracket_width) x rate
    """
    if pkp <= Decimal("0"):
        return Decimal("0")

    total_tax = Decimal("0")
    remaining = pkp

    for bracket in sorted(brackets, key=lambda b: b.lower_bound):
        if remaining <= Decimal("0"):
            break
        bracket_width = bracket.upper_bound - bracket.lower_bound
        taxable_in_bracket = min(remaining, bracket_width)
        total_tax += taxable_in_bracket * bracket.rate
        remaining -= taxable_in_bracket

    return total_tax


def calculate_monthly_pph21_pasal17(
    monthly_gross: Decimal,
    monthly_bpjs_jht_employee: Decimal,
    monthly_bpjs_jp_employee: Decimal,
    ptkp_annual: Decimal,
    brackets: List[TaxBracket],
) -> Decimal:
    """Calculate monthly PPh 21 using Pasal 17 method.

    Steps:
    1. Annualize gross income
    2. Calculate biaya jabatan
    3. Calculate annual BPJS deductible
    4. Calculate PKP
    5. Apply progressive brackets
    6. Divide by 12 for monthly amount

    Args:
        monthly_gross: Total monthly gross income (salary + taxable allowances + OT + bonus)
        monthly_bpjs_jht_employee: Monthly BPJS JHT employee contribution
        monthly_bpjs_jp_employee: Monthly BPJS JP employee contribution
        ptkp_annual: Annual PTKP amount based on employee's status (TK/0, K/1, etc.)
        brackets: List of progressive tax brackets

    Returns:
        Monthly PPh 21 tax amount (rounded to nearest Rupiah)
    """
    annual_gross = monthly_gross * Decimal("12")
    biaya_jabatan = calculate_biaya_jabatan(annual_gross)
    annual_bpjs = calculate_annual_bpjs_deductible(
        monthly_bpjs_jht_employee, monthly_bpjs_jp_employee
    )
    pkp = calculate_pkp(annual_gross, biaya_jabatan, annual_bpjs, ptkp_annual)
    annual_tax = apply_progressive_brackets(pkp, brackets)
    monthly_tax = annual_tax / Decimal("12")

    from app.utils.decimal_utils import round_money

    return round_money(monthly_tax)
"""
PPh 21 Pasal 17 progressive tax calculation.
Provides TaxBracket dataclass and calculation logic.
"""
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional


@dataclass
class TaxBracket:
    """A single progressive tax bracket for Pasal 17 calculation."""
    lower_bound: Decimal
    upper_bound: Optional[Decimal]  # None means no upper limit
    rate: Decimal
