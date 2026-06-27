"""
Rules Engine for dynamic payroll calculations.

Provides a safe formula evaluator and helpers to fetch active rules.
Rules are optional overrides; callers should fall back to existing config
when a rule is not found or not applicable.
"""

import re
import logging
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import date
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session

from app.models.rules import RuleConfiguration, RuleVariable

logger = logging.getLogger(__name__)


class RulesEngineError(Exception):
    """Raised when a rule cannot be evaluated."""

    pass


class RulesEngine:
    """Evaluate dynamic payroll rules stored in rule_configurations."""

    ALLOWED_FORMULA_CHARS = set("0123456789.+-*/() ")

    def __init__(self, db: Session):
        self.db = db
        self._cache: Dict[str, Optional[RuleConfiguration]] = {}

    def _cache_key(self, company_id: int, rule_code: str, effective_date: date) -> str:
        return f"{company_id}:{rule_code}:{effective_date.isoformat()}"

    def clear_cache(self) -> None:
        """Clear the in-memory rule cache."""
        self._cache.clear()

    def get_active_rule(
        self,
        company_id: int,
        rule_code: str,
        effective_date: Optional[date] = None,
    ) -> Optional[RuleConfiguration]:
        """Fetch the active rule for a given rule_code and date.

        Returns the highest-priority rule when multiple rules match.
        """
        if effective_date is None:
            effective_date = date.today()

        key = self._cache_key(company_id, rule_code, effective_date)
        if key in self._cache:
            return self._cache[key]

        rule = (
            self.db.query(RuleConfiguration)
            .filter(
                RuleConfiguration.company_id == company_id,
                RuleConfiguration.rule_code == rule_code,
                RuleConfiguration.is_active == True,
                RuleConfiguration.effective_date <= effective_date,
            )
            .filter(
                (RuleConfiguration.expiry_date.is_(None))
                | (RuleConfiguration.expiry_date >= effective_date)
            )
            .order_by(RuleConfiguration.priority.desc())
            .first()
        )

        self._cache[key] = rule
        return rule

    def get_active_brackets(
        self,
        company_id: int,
        rule_code_prefix: str,
        effective_date: Optional[date] = None,
    ) -> List[RuleConfiguration]:
        """Fetch active BRACKET rules matching a rule_code prefix."""
        if effective_date is None:
            effective_date = date.today()

        return (
            self.db.query(RuleConfiguration)
            .filter(
                RuleConfiguration.company_id == company_id,
                RuleConfiguration.rule_code.like(f"{rule_code_prefix}%"),
                RuleConfiguration.rule_type == "BRACKET",
                RuleConfiguration.is_active == True,
                RuleConfiguration.effective_date <= effective_date,
            )
            .filter(
                (RuleConfiguration.expiry_date.is_(None))
                | (RuleConfiguration.expiry_date >= effective_date)
            )
            .order_by(RuleConfiguration.min_value.asc())
            .all()
        )

    def evaluate_formula(self, formula: str, context: Dict[str, Any]) -> Decimal:
        """Safely evaluate a formula using only numeric operators and whitelisted variables.

        Args:
            formula: Mathematical expression, e.g. "basic_salary * 0.01".
            context: Mapping of variable names to numeric values.

        Returns:
            Decimal result rounded to 2 decimal places.

        Raises:
            RulesEngineError: If the formula contains invalid syntax or unknown variables.
        """
        if not formula or not formula.strip():
            raise RulesEngineError("Formula is empty")

        formula_vars = set(re.findall(r"\b[a-z_][a-z0-9_]*\b", formula))
        allowed_vars = set(context.keys())
        unknown = formula_vars - allowed_vars
        if unknown:
            raise RulesEngineError(f"Unknown variables in formula: {unknown}")

        # Verify the formula only contains safe characters plus allowed variable names
        remaining = formula
        for var in sorted(formula_vars, key=len, reverse=True):
            remaining = remaining.replace(var, "")
        if not set(remaining).issubset(self.ALLOWED_FORMULA_CHARS):
            raise RulesEngineError("Formula contains invalid characters")

        # Substitute variables with their values
        eval_formula = formula
        for var in formula_vars:
            value = context.get(var)
            if value is None:
                raise RulesEngineError(f"Variable '{var}' value is missing")
            eval_formula = eval_formula.replace(var, str(value))

        try:
            result = eval(eval_formula, {"__builtins__": {}}, {})
            return Decimal(str(result)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (SyntaxError, NameError, TypeError, ZeroDivisionError, InvalidOperation) as exc:
            raise RulesEngineError(f"Error evaluating formula '{formula}': {exc}") from exc

    def evaluate_constant(
        self,
        company_id: int,
        rule_code: str,
        effective_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Evaluate a CONSTANT rule."""
        rule = self.get_active_rule(company_id, rule_code, effective_date)
        if rule is None or rule.rule_type != "CONSTANT":
            return None
        if rule.value is None:
            raise RulesEngineError(f"CONSTANT rule '{rule_code}' has no value")
        return Decimal(str(rule.value))

    def evaluate_formula_rule(
        self,
        company_id: int,
        rule_code: str,
        context: Dict[str, Any],
        effective_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Evaluate a FORMULA rule."""
        rule = self.get_active_rule(company_id, rule_code, effective_date)
        if rule is None or rule.rule_type != "FORMULA":
            return None
        if not rule.formula:
            raise RulesEngineError(f"FORMULA rule '{rule_code}' has no formula")
        return self.evaluate_formula(rule.formula, context)

    def evaluate_bracket(
        self,
        company_id: int,
        rule_code_prefix: str,
        amount: Decimal,
        effective_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Find matching BRACKET and return amount * rate.

        Returns None if no bracket matches or no rules exist.
        """
        brackets = self.get_active_brackets(company_id, rule_code_prefix, effective_date)
        if not brackets:
            return None

        amount_dec = Decimal(str(amount))
        for bracket in brackets:
            min_val = Decimal(str(bracket.min_value)) if bracket.min_value else Decimal("0")
            max_val = Decimal(str(bracket.max_value)) if bracket.max_value else None
            if amount_dec >= min_val and (max_val is None or amount_dec <= max_val):
                if bracket.rate is None:
                    raise RulesEngineError(f"Bracket rule '{bracket.rule_code}' has no rate")
                return (amount_dec * Decimal(str(bracket.rate))).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
        return None

    # ─── Convenience helpers for payroll integration ───────────────────────────

    def evaluate_bpjs(
        self,
        company_id: int,
        rule_code: str,
        basic_salary: Decimal,
        effective_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Evaluate a BPJS rule. Supports CONSTANT and FORMULA types with ceiling."""
        rule = self.get_active_rule(company_id, rule_code, effective_date)
        if rule is None:
            return None

        if rule.rule_type == "CONSTANT":
            return self.evaluate_constant(company_id, rule_code, effective_date)

        if rule.rule_type == "FORMULA":
            context = {"basic_salary": basic_salary}
            return self.evaluate_formula(rule.formula, context)

        raise RulesEngineError(f"Unsupported BPJS rule type: {rule.rule_type}")

    def evaluate_pph21_ter(
        self,
        company_id: int,
        monthly_income: Decimal,
        ptkp_category: str,
        effective_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Evaluate PPh 21 TER using bracket rules.

        Looks for rules with code prefix PPH21_TER_{ptkp_category}_
        """
        prefix = f"PPH21_TER_{ptkp_category}_"
        return self.evaluate_bracket(company_id, prefix, monthly_income, effective_date)

    def evaluate_pph21_pasal17(
        self,
        company_id: int,
        pkp: Decimal,
        effective_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Evaluate PPh 21 Pasal 17 progressive tax.

        Looks for rules with code prefix PPH21_PASAL17_BRACKET_
        Returns annual tax or None if no rules exist.
        """
        brackets = self.get_active_brackets(company_id, "PPH21_PASAL17_BRACKET_", effective_date)
        if not brackets:
            return None

        total_tax = Decimal("0")
        remaining = Decimal(str(pkp))

        for bracket in brackets:
            if remaining <= 0:
                break
            min_val = Decimal(str(bracket.min_value)) if bracket.min_value else Decimal("0")
            max_val = Decimal(str(bracket.max_value)) if bracket.max_value else None
            rate = Decimal(str(bracket.rate)) if bracket.rate else Decimal("0")

            taxable_in_bracket = remaining
            if max_val is not None:
                taxable_in_bracket = min(remaining, max_val - min_val)
            total_tax += (taxable_in_bracket * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            remaining -= taxable_in_bracket

        return total_tax

    def evaluate_overtime_multiplier(
        self,
        company_id: int,
        rule_code: str,
        effective_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Evaluate an overtime multiplier CONSTANT rule."""
        return self.evaluate_constant(company_id, rule_code, effective_date)

    def get_lookup_value(
        self,
        company_id: int,
        rule_code: str,
        effective_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Evaluate a LOOKUP_TABLE rule returning its constant value."""
        rule = self.get_active_rule(company_id, rule_code, effective_date)
        if rule is None or rule.rule_type != "LOOKUP_TABLE":
            return None
        if rule.value is None:
            raise RulesEngineError(f"LOOKUP_TABLE rule '{rule_code}' has no value")
        return Decimal(str(rule.value))
