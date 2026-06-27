"""
Integration wrappers that let the Rules Engine optionally override existing
payroll configuration tables without replacing them.

When a matching active rule exists in rule_configurations, it is used.
Otherwise the function returns None and the caller should fall back to the
standard config tables (BpjsSetting, TaxBracketPasal17, TerBracket, OvertimeSetting).
"""

from decimal import Decimal
from datetime import date
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.tax import TaxBracketPasal17, TerBracket
from app.models.bpjs import BpjsSetting
from app.services.rules_engine import RulesEngine


def _to_decimal(value) -> Optional[Decimal]:
    if value is None:
        return None
    return Decimal(str(value))


def get_bpjs_config_or_default(
    db: Session,
    bpjs_type: str,
    company_id: int,
    period_date: date,
) -> Optional[dict]:
    """Return BPJS config from Rules Engine or None to use existing BpjsSetting."""
    engine = RulesEngine(db)

    employee_rate = engine.evaluate_constant(
        company_id, f"BPJS_{bpjs_type}_EMPLOYEE_RATE", period_date
    )
    employer_rate = engine.evaluate_constant(
        company_id, f"BPJS_{bpjs_type}_EMPLOYER_RATE", period_date
    )
    ceiling = engine.evaluate_constant(
        company_id, f"BPJS_{bpjs_type}_CEILING", period_date
    )

    if employee_rate is None and employer_rate is None and ceiling is None:
        return None

    # Fall back to existing table for any missing rate
    existing = (
        db.query(BpjsSetting)
        .filter(
            BpjsSetting.company_id == company_id,
            BpjsSetting.bpjs_type == bpjs_type,
            BpjsSetting.is_active == True,
            BpjsSetting.effective_date <= period_date,
        )
        .order_by(BpjsSetting.effective_date.desc())
        .first()
    )

    return {
        "bpjs_type": bpjs_type,
        "employee_rate": employee_rate if employee_rate is not None else (
            _to_decimal(existing.employee_rate) if existing else Decimal("0")
        ),
        "employer_rate": employer_rate if employer_rate is not None else (
            _to_decimal(existing.employer_rate) if existing else Decimal("0")
        ),
        "max_salary_base": ceiling if ceiling is not None else (
            _to_decimal(existing.max_salary_base) if existing else None
        ),
    }


def get_tax_method_or_default(
    db: Session,
    company_id: int,
    period_date: date,
    default_method: str = "PASAL_17",
) -> str:
    """Return tax calculation method from Rules Engine or default."""
    engine = RulesEngine(db)
    rule = engine.get_active_rule(company_id, "PPH21_TAX_METHOD", period_date)
    if rule and rule.rule_type == "CONSTANT" and rule.value:
        method = str(rule.value).strip().upper()
        if method in ("PASAL_17", "TER"):
            return method
    return default_method


def get_pasal17_brackets_or_default(
    db: Session,
    company_id: int,
    period_date: date,
) -> Optional[List[dict]]:
    """Return Pasal 17 brackets from Rules Engine or None to use existing table."""
    engine = RulesEngine(db)
    brackets = engine.get_active_brackets(company_id, "PPH21_PASAL17_BRACKET_", period_date)
    if not brackets:
        return None

    return [
        {
            "lower_bound": _to_decimal(b.min_value) or Decimal("0"),
            "upper_bound": _to_decimal(b.max_value),
            "rate": _to_decimal(b.rate) or Decimal("0"),
        }
        for b in brackets
    ]


def get_ter_brackets_or_default(
    db: Session,
    company_id: int,
    category: str,
    period_date: date,
) -> Optional[List[dict]]:
    """Return TER brackets for a category from Rules Engine or None to use existing table."""
    engine = RulesEngine(db)
    brackets = engine.get_active_brackets(
        company_id, f"PPH21_TER_{category}_", period_date
    )
    if not brackets:
        return None

    return [
        {
            "category": category,
            "income_range_min": _to_decimal(b.min_value) or Decimal("0"),
            "income_range_max": _to_decimal(b.max_value),
            "ter_rate": _to_decimal(b.rate) or Decimal("0"),
        }
        for b in brackets
    ]


def get_ptkp_value_or_default(
    db: Session,
    company_id: int,
    ptkp_code: str,
    period_date: date,
) -> Optional[Decimal]:
    """Return annual PTKP value from Rules Engine or None to use existing table."""
    engine = RulesEngine(db)
    value = engine.evaluate_constant(
        company_id, f"PTKP_{ptkp_code.replace('/', '_')}_ANNUAL", period_date
    )
    return value


def get_overtime_multiplier_or_default(
    db: Session,
    company_id: int,
    rule_code: str,
    period_date: date,
) -> Optional[Decimal]:
    """Return overtime multiplier from Rules Engine or None to use hard-coded defaults."""
    engine = RulesEngine(db)
    return engine.evaluate_constant(company_id, rule_code, period_date)


def get_hourly_divisor_or_default(
    db: Session,
    company_id: int,
    period_date: date,
    default_divisor: Decimal = Decimal("173"),
) -> Decimal:
    """Return monthly working hours divisor from Rules Engine or default 173."""
    engine = RulesEngine(db)
    value = engine.evaluate_constant(company_id, "OVERTIME_HOURLY_DIVISOR", period_date)
    return value if value is not None else default_divisor
