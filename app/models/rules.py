"""
Rules Engine models for dynamic payroll configuration.

Tables:
- rule_categories: Grouping of rules by functional area.
- rule_configurations: Actual configurable rules/formulas/brackets.
- rule_variables: Whitelisted variables available to formulas.
- rule_audit_logs: Audit trail of rule changes.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class RuleCategory(Base, TimestampMixin):
    """Functional grouping for rules (BPJS, PPh21, Overtime, Allowance)."""

    __tablename__ = "rule_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_code = Column(String(50), unique=True, nullable=False)
    category_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    rules = relationship("RuleConfiguration", backref="category", lazy="select")


class RuleConfiguration(Base, TimestampMixin):
    """A single configurable payroll rule."""

    __tablename__ = "rule_configurations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("rule_categories.id"), nullable=False)
    rule_code = Column(String(100), nullable=False)
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(20), nullable=False)
    formula = Column(Text, nullable=True)
    value = Column(Numeric(18, 2), nullable=True)
    min_value = Column(Numeric(18, 2), nullable=True)
    max_value = Column(Numeric(18, 2), nullable=True)
    rate = Column(Numeric(10, 4), nullable=True)
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], lazy="select")
    updater = relationship("User", foreign_keys=[updated_by], lazy="select")
    audits = relationship("RuleAuditLog", backref="rule", lazy="select")

    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('FORMULA', 'CONSTANT', 'BRACKET', 'LOOKUP_TABLE')",
            name="ck_rule_configurations_rule_type",
        ),
        UniqueConstraint(
            "company_id", "rule_code", "effective_date",
            name="uq_rule_configurations_company_code_date",
        ),
        Index("idx_rule_configurations_lookup", "company_id", "rule_code", "is_active", "effective_date", "expiry_date"),
        Index("idx_rule_configurations_category", "category_id"),
    )


class RuleVariable(Base, TimestampMixin):
    """Whitelisted variable available to formulas in the Rules Engine."""

    __tablename__ = "rule_variables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    variable_code = Column(String(100), unique=True, nullable=False)
    variable_name = Column(String(255), nullable=False)
    variable_type = Column(String(30), nullable=False)
    source_table = Column(String(100), nullable=True)
    source_field = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "variable_type IN ('EMPLOYEE_FIELD', 'CALCULATED', 'SYSTEM_CONSTANT')",
            name="ck_rule_variables_variable_type",
        ),
    )


class RuleAuditLog(Base):
    """Audit trail of rule configuration changes."""

    __tablename__ = "rule_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey("rule_configurations.id"), nullable=False)
    action = Column(String(20), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, nullable=False, default="CURRENT_TIMESTAMP")
    reason = Column(Text, nullable=True)

    changer = relationship("User", foreign_keys=[changed_by], lazy="select")

    __table_args__ = (
        CheckConstraint(
            "action IN ('CREATE', 'UPDATE', 'DELETE', 'ACTIVATE', 'DEACTIVATE')",
            name="ck_rule_audit_logs_action",
        ),
        Index("idx_rule_audit_logs_rule", "rule_id", "changed_at"),
    )
