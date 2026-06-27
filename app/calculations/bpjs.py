"""
BPJS (Badan Penyelenggara Jaminan Sosial) contribution calculation.
All functions are PURE — no DB access, no side effects.

Types and standard rates:
- KESEHATAN: 5% (4% employer, 1% employee), salary cap 12,000,000
- JHT: 5.7% (3.7% employer, 2% employee), no default cap
- JP: 3% (2% employer, 1% employee), salary cap ~9,559,600 (updated annually)
- JKK: employer only (0.24% - 1.74% based on risk class), no cap
- JKM: employer only (0.3%), no cap

Calculation:
- base = base_salary + sum(allowances where is_bpjs_base=True)
- If max_salary_base is set, effective_base = min(calc_base, max_salary_base)
- contribution = effective_base × rate
"""
from decimal import Decimal
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class BpjsConfig:
    """In-memory BPJS setting for a single type."""

    bpjs_type: str
    employee_rate: Decimal
    employer_rate: Decimal
    max_salary_base: Optional[Decimal]  # None means no cap


@dataclass
class BpjsResult:
    """Complete BPJS calculation result for one employee."""

    kes_employee: Decimal
    kes_employer: Decimal
    jht_employee: Decimal
    jht_employer: Decimal
    jp_employee: Decimal
    jp_employer: Decimal
    jkk_employer: Decimal
    jkm_employer: Decimal

    @property
    def total_employee(self) -> Decimal:
        """Total employee BPJS deduction (KES + JHT + JP)."""
        return self.kes_employee + self.jht_employee + self.jp_employee

    @property
    def total_employer(self) -> Decimal:
        """Total employer BPJS cost (KES + JHT + JP + JKK + JKM)."""
        return (
            self.kes_employer
            + self.jht_employer
            + self.jp_employer
            + self.jkk_employer
            + self.jkm_employer
        )


def calculate_bpjs_base(
    base_salary: Decimal, allowances_bpjs_base: Decimal
) -> Decimal:
    """Calculate BPJS contribution base = base salary + BPJS-eligible allowances.

    Args:
        base_salary: Employee's base salary
        allowances_bpjs_base: Sum of allowances flagged as is_bpjs_base=True

    Returns:
        BPJS calculation base amount
    """
    return base_salary + allowances_bpjs_base


def calculate_bpjs_contribution(
    calc_base: Decimal, rate: Decimal, max_salary_base: Optional[Decimal]
) -> Decimal:
    """Calculate single BPJS contribution with salary cap.

    Args:
        calc_base: BPJS calculation base (salary + BPJS-eligible allowances)
        rate: Contribution rate as Decimal (e.g., Decimal("0.01") for 1%)
        max_salary_base: Maximum salary base for this BPJS type (None = no cap)

    Returns:
        Contribution amount rounded to nearest Rupiah
    """
    from app.utils.decimal_utils import round_money

    effective_base = min(calc_base, max_salary_base) if max_salary_base else calc_base
    return round_money(effective_base * rate)


def calculate_all_bpjs(
    calc_base: Decimal, bpjs_settings: Dict[str, BpjsConfig]
) -> BpjsResult:
    """Calculate all BPJS contributions for an employee.

    Handles missing BPJS types gracefully by returning 0 for unconfigured types.
    This allows partial enrollment (e.g., employee not enrolled in JP).

    Args:
        calc_base: base_salary + BPJS-eligible allowances
        bpjs_settings: dict mapping bpjs_type (e.g., "KESEHATAN") -> BpjsConfig

    Returns:
        BpjsResult with all employee and employer contributions

    Raises:
        BpjsCalculationError: If calc_base is negative
    """
    from app.exceptions import BpjsCalculationError

    if calc_base < Decimal("0"):
        raise BpjsCalculationError(
            f"BPJS calculation base cannot be negative: {calc_base}"
        )

    def get_contribution(bpjs_type: str, is_employee: bool) -> Decimal:
        config = bpjs_settings.get(bpjs_type)
        if not config:
            return Decimal("0")
        rate = config.employee_rate if is_employee else config.employer_rate
        return calculate_bpjs_contribution(calc_base, rate, config.max_salary_base)

    return BpjsResult(
        kes_employee=get_contribution("KESEHATAN", True),
        kes_employer=get_contribution("KESEHATAN", False),
        jht_employee=get_contribution("JHT", True),
        jht_employer=get_contribution("JHT", False),
        jp_employee=get_contribution("JP", True),
        jp_employer=get_contribution("JP", False),
        jkk_employer=get_contribution("JKK", False),
        jkm_employer=get_contribution("JKM", False),
    )
