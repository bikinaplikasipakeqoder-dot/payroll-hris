"""
Core Calculation Engines for Indonesian Payroll & HRIS.

All functions are PURE and STATELESS — no database access, no side effects.
All monetary values use Decimal — NEVER float.

Modules:
- pph21_pasal17: PPh 21 progressive tax calculation (UU HPP / Pasal 17)
- pph21_ter: PPh 21 TER method (PMK 168/2023)
- bpjs: BPJS contribution calculation (Kesehatan, JHT, JP, JKK, JKM)
- overtime: Overtime calculation per Permenaker
- allowance: Allowance aggregation with taxable/BPJS base flags
- gross_nett: Gross vs Nett (gross-up) payroll method
"""

# PPh 21 Pasal 17 — Progressive Tax
from app.calculations.pph21_pasal17 import (
    TaxBracket,
    BIAYA_JABATAN_RATE,
    BIAYA_JABATAN_MAX_ANNUAL,
    BIAYA_JABATAN_MAX_MONTHLY,
    calculate_biaya_jabatan,
    calculate_annual_bpjs_deductible,
    calculate_pkp,
    apply_progressive_brackets,
    calculate_monthly_pph21_pasal17,
)

# PPh 21 TER — Tarif Efektif Rata-rata
from app.calculations.pph21_ter import (
    TerBracketData,
    PTKP_TO_TER_CATEGORY,
    get_ter_category,
    find_ter_rate,
    calculate_monthly_pph21_ter,
    calculate_december_reconciliation,
)

# BPJS Contributions
from app.calculations.bpjs import (
    BpjsConfig,
    BpjsResult,
    calculate_bpjs_base,
    calculate_bpjs_contribution,
    calculate_all_bpjs,
)

# Overtime
from app.calculations.overtime import (
    OvertimeEntry,
    HOURLY_DIVISOR,
    calculate_hourly_rate,
    get_multiplier_5day,
    get_multiplier_6day,
    calculate_single_overtime,
    calculate_overtime_total,
)

# Allowances
from app.calculations.allowance import (
    AllowanceEntry,
    AllowanceResult,
    calculate_allowance_amount,
    calculate_all_allowances,
)

# Gross / Nett Method
from app.calculations.gross_nett import (
    MAX_ITERATIONS,
    CONVERGENCE_TOLERANCE,
    calculate_gross_method,
    calculate_nett_method_grossup,
)

__all__ = [
    # PPh 21 Pasal 17
    "TaxBracket",
    "BIAYA_JABATAN_RATE",
    "BIAYA_JABATAN_MAX_ANNUAL",
    "BIAYA_JABATAN_MAX_MONTHLY",
    "calculate_biaya_jabatan",
    "calculate_annual_bpjs_deductible",
    "calculate_pkp",
    "apply_progressive_brackets",
    "calculate_monthly_pph21_pasal17",
    # PPh 21 TER
    "TerBracketData",
    "PTKP_TO_TER_CATEGORY",
    "get_ter_category",
    "find_ter_rate",
    "calculate_monthly_pph21_ter",
    "calculate_december_reconciliation",
    # BPJS
    "BpjsConfig",
    "BpjsResult",
    "calculate_bpjs_base",
    "calculate_bpjs_contribution",
    "calculate_all_bpjs",
    # Overtime
    "OvertimeEntry",
    "HOURLY_DIVISOR",
    "calculate_hourly_rate",
    "get_multiplier_5day",
    "get_multiplier_6day",
    "calculate_single_overtime",
    "calculate_overtime_total",
    # Allowances
    "AllowanceEntry",
    "AllowanceResult",
    "calculate_allowance_amount",
    "calculate_all_allowances",
    # Gross / Nett
    "MAX_ITERATIONS",
    "CONVERGENCE_TOLERANCE",
    "calculate_gross_method",
    "calculate_nett_method_grossup",
]
