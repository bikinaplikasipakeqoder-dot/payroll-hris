"""
Allowance calculation and aggregation.
All functions are PURE — no DB access, no side effects.

AllowanceType.calculation_type:
- FIXED: Use amount directly
- PERCENTAGE: amount is percentage of base_salary
- FORMULA: Not implemented in v1 (reserved for future — treated as FIXED)

Flags:
- is_taxable: Include in gross taxable income for PPh 21 calculation
- is_bpjs_base: Include in BPJS calculation base
"""
from decimal import Decimal
from typing import List
from dataclasses import dataclass


@dataclass
class AllowanceEntry:
    """Represents a single employee allowance for calculation."""

    name: str
    code: str
    calculation_type: str  # FIXED, PERCENTAGE, FORMULA
    amount: Decimal  # Direct amount (IDR) or percentage value (e.g., 10 for 10%)
    is_taxable: bool
    is_bpjs_base: bool


@dataclass
class AllowanceResult:
    """Aggregated allowance calculation result."""

    total_allowances: Decimal
    total_taxable: Decimal
    total_non_taxable: Decimal
    total_bpjs_base: Decimal
    details: List[dict]  # For payslip detail JSON


def calculate_allowance_amount(entry: AllowanceEntry, base_salary: Decimal) -> Decimal:
    """Calculate actual allowance amount based on calculation type.

    Args:
        entry: Allowance configuration entry
        base_salary: Employee's base salary (used for PERCENTAGE type)

    Returns:
        Calculated allowance amount rounded to nearest Rupiah

    Calculation types:
    - FIXED: returns entry.amount directly
    - PERCENTAGE: returns base_salary × (entry.amount / 100)
    - FORMULA: reserved for future, treated as FIXED in v1
    """
    from app.utils.decimal_utils import round_money

    if entry.calculation_type == "FIXED":
        return round_money(entry.amount)
    elif entry.calculation_type == "PERCENTAGE":
        return round_money(base_salary * entry.amount / Decimal("100"))
    elif entry.calculation_type == "FORMULA":
        # Formula evaluation reserved for future implementation
        # For now, treat as fixed amount
        return round_money(entry.amount)
    else:
        return Decimal("0")


def calculate_all_allowances(
    entries: List[AllowanceEntry], base_salary: Decimal
) -> AllowanceResult:
    """Calculate and aggregate all allowances for an employee.

    Iterates through all allowance entries, calculates each amount,
    and aggregates by taxable/non-taxable and BPJS base categories.

    Args:
        entries: List of allowance entries for the employee
        base_salary: Employee's base salary

    Returns:
        AllowanceResult with totals broken down by taxable/non-taxable and BPJS base,
        plus a details list suitable for payslip JSON output.
    """
    total = Decimal("0")
    taxable = Decimal("0")
    non_taxable = Decimal("0")
    bpjs_base = Decimal("0")
    details = []

    for entry in entries:
        amount = calculate_allowance_amount(entry, base_salary)
        total += amount

        if entry.is_taxable:
            taxable += amount
        else:
            non_taxable += amount

        if entry.is_bpjs_base:
            bpjs_base += amount

        details.append(
            {
                "name": entry.name,
                "code": entry.code,
                "amount": str(amount),
                "is_taxable": entry.is_taxable,
                "is_bpjs_base": entry.is_bpjs_base,
            }
        )

    return AllowanceResult(
        total_allowances=total,
        total_taxable=taxable,
        total_non_taxable=non_taxable,
        total_bpjs_base=bpjs_base,
        details=details,
    )
