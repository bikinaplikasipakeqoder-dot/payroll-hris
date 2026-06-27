"""
Configuration loader service.
Loads all payroll configuration (tax, BPJS, overtime settings) in a single
batch query per payroll run. Returns frozen dataclasses for use in calculations.
"""
from decimal import Decimal
from datetime import date
from typing import List, Dict
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.tax import TaxSetting, PtkpValue, TaxBracketPasal17, TerBracket
from app.models.bpjs import BpjsSetting
from app.models.attendance import OvertimeSetting
from app.exceptions import InsufficientConfigError
from app.utils.decimal_utils import to_decimal

# Import calculation dataclasses
from app.calculations.pph21_pasal17 import TaxBracket
from app.calculations.pph21_ter import TerBracketData
from app.calculations.bpjs import BpjsConfig


@dataclass
class PayrollConfig:
    """Frozen configuration snapshot for a payroll run."""
    tax_method: str  # PASAL_17 or TER
    ptkp_values: Dict[str, Decimal]  # ptkp_code -> annual_amount
    tax_brackets: List[TaxBracket]  # Sorted by lower_bound
    ter_brackets: List[TerBracketData]  # All categories
    bpjs_settings: Dict[str, BpjsConfig]  # bpjs_type -> config
    work_week_type: str  # 5_DAY or 6_DAY


class ConfigLoader:
    """Loads payroll configuration from database."""

    @staticmethod
    def load(company_id: int, period_date: date, session: Session) -> PayrollConfig:
        """Load all payroll configuration for a company.

        Queries:
        1. Tax settings (method)
        2. PTKP values (active for period)
        3. Tax brackets Pasal 17 (active for period)
        4. TER brackets (active for period)
        5. BPJS settings (active for period)
        6. Overtime settings (active for company)

        Raises InsufficientConfigError if any required config is missing.
        """
        # Load tax method
        tax_setting = session.query(TaxSetting).filter(
            TaxSetting.company_id == company_id,
            TaxSetting.is_active == True,
        ).first()
        if not tax_setting:
            raise InsufficientConfigError(
                "No active tax settings found", {"company_id": company_id}
            )

        # Load PTKP values
        ptkp_rows = session.query(PtkpValue).filter(
            PtkpValue.company_id == company_id,
            PtkpValue.is_active == True,
            PtkpValue.effective_date <= period_date,
        ).all()
        if not ptkp_rows:
            raise InsufficientConfigError(
                "No active PTKP values found", {"company_id": company_id}
            )
        ptkp_values = {row.ptkp_code: to_decimal(row.annual_amount) for row in ptkp_rows}

        # Load Pasal 17 brackets
        bracket_rows = session.query(TaxBracketPasal17).filter(
            TaxBracketPasal17.company_id == company_id,
            TaxBracketPasal17.is_active == True,
            TaxBracketPasal17.effective_date <= period_date,
        ).order_by(TaxBracketPasal17.bracket_order).all()
        if not bracket_rows:
            raise InsufficientConfigError(
                "No active tax brackets found", {"company_id": company_id}
            )
        tax_brackets = [
            TaxBracket(
                lower_bound=to_decimal(row.income_range_min),
                upper_bound=to_decimal(row.income_range_max) if row.income_range_max else None,
                rate=to_decimal(row.tax_rate),
            )
            for row in bracket_rows
        ]

        # Load TER brackets
        ter_rows = session.query(TerBracket).filter(
            TerBracket.company_id == company_id,
            TerBracket.is_active == True,
            TerBracket.effective_date <= period_date,
        ).all()
        ter_brackets = [
            TerBracketData(
                category=row.category,
                income_range_min=to_decimal(row.income_range_min),
                income_range_max=to_decimal(row.income_range_max),
                ter_rate=to_decimal(row.ter_rate),
            )
            for row in ter_rows
        ]

        # Load BPJS settings
        bpjs_rows = session.query(BpjsSetting).filter(
            BpjsSetting.company_id == company_id,
            BpjsSetting.is_active == True,
            BpjsSetting.effective_date <= period_date,
        ).all()
        if not bpjs_rows:
            raise InsufficientConfigError(
                "No active BPJS settings found", {"company_id": company_id}
            )
        bpjs_settings = {
            row.bpjs_type: BpjsConfig(
                bpjs_type=row.bpjs_type,
                employee_rate=to_decimal(row.employee_rate),
                employer_rate=to_decimal(row.employer_rate),
                max_salary_base=to_decimal(row.max_salary_base) if row.max_salary_base else None,
            )
            for row in bpjs_rows
        }

        # Load overtime settings (no effective_date on this model — single config per company)
        ot_setting = session.query(OvertimeSetting).filter(
            OvertimeSetting.company_id == company_id,
            OvertimeSetting.is_active == True,
        ).first()
        work_week_type = ot_setting.work_week_type if ot_setting else "5_DAY"

        return PayrollConfig(
            tax_method=tax_setting.tax_calculation_method,
            ptkp_values=ptkp_values,
            tax_brackets=tax_brackets,
            ter_brackets=ter_brackets,
            bpjs_settings=bpjs_settings,
            work_week_type=work_week_type,
        )
