"""
Bonus, THR, and reimbursement models for the Payroll & HRIS system.

Tables:
- bonus_types: Types of bonuses available
- bonuses: Individual bonus awards to employees
- thr_records: Tunjangan Hari Raya (THR) records per employee
- reimbursement_types: Types of reimbursements
- reimbursements: Employee reimbursement claims
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class BonusType(Base, TimestampMixin):
    """Types of bonuses available in a company."""

    __tablename__ = "bonus_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    is_taxable = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    bonuses = relationship("Bonus", backref="bonus_type")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_bonus_types_company_code"),
    )


class Bonus(Base, TimestampMixin):
    """Individual bonus awards to employees."""

    __tablename__ = "bonuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    bonus_type_id = Column(Integer, ForeignKey("bonus_types.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    bonus_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    approval_status = Column(String(20), nullable=False, default="PENDING")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=True)
    is_processed = Column(Boolean, default=False)

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_bonuses_amount_positive",
        ),
        CheckConstraint(
            "approval_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_bonuses_approval_status",
        ),
        Index("idx_bonuses_employee", "employee_id"),
        Index("idx_bonuses_date", "bonus_date"),
    )


class THRConfig(Base, TimestampMixin):
    """Company-level THR payment configuration.

    - payment_mode:
        * BY_RELIGION: each employee receives THR on their own religious holiday
        * UNIFIED: all active employees receive THR together on the configured
                   unified_holiday date (commonly Idul Fitri)
    - unified_holiday: the holiday used when payment_mode is UNIFIED
    - full_tenure_months: tenure threshold for full (1x base salary) THR
    - min_tenure_months: minimum tenure (in months) to be eligible for prorated THR
    - prorate_partial_months: whether a partial month counts as a full month
    """

    __tablename__ = "thr_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, unique=True)
    payment_mode = Column(String(20), nullable=False, default="BY_RELIGION")
    unified_holiday = Column(String(20), nullable=False, default="IDUL_FITRI")
    full_tenure_months = Column(Integer, nullable=False, default=12)
    min_tenure_months = Column(Integer, nullable=False, default=1)
    prorate_partial_months = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "payment_mode IN ('BY_RELIGION', 'UNIFIED')",
            name="ck_thr_configs_payment_mode",
        ),
        CheckConstraint(
            "unified_holiday IN ('IDUL_FITRI', 'CHRISTMAS', 'NYEPI', 'WAISAK')",
            name="ck_thr_configs_unified_holiday",
        ),
        CheckConstraint("full_tenure_months >= 1", name="ck_thr_configs_full_tenure"),
        CheckConstraint("min_tenure_months >= 0", name="ck_thr_configs_min_tenure"),
    )


class THRRecord(Base, TimestampMixin):
    """Tunjangan Hari Raya (THR) records per employee.

    THR timing follows religious holidays:
    - IDUL_FITRI: Muslim employees, paid before Eid al-Fitr
    - CHRISTMAS: Christian employees, paid before Christmas
    - NYEPI: Hindu employees, paid before Nyepi (Day of Silence)
    - WAISAK: Buddhist employees, paid before Waisak
    """

    __tablename__ = "thr_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    thr_year = Column(Integer, nullable=False)
    religious_holiday = Column(String(20), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    thr_date = Column(Date, nullable=False)
    calculation_basis = Column(String(20), nullable=False, default="BASE_SALARY")
    tenure_months = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="DRAFT")
    description = Column(Text, nullable=True)
    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=True)
    is_processed = Column(Boolean, default=False)

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_thr_records_amount"),
        CheckConstraint(
            "religious_holiday IN ('IDUL_FITRI', 'CHRISTMAS', 'NYEPI', 'WAISAK')",
            name="ck_thr_records_religious_holiday",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'APPROVED', 'PAID')",
            name="ck_thr_records_status",
        ),
        CheckConstraint(
            "calculation_basis IN ('BASE_SALARY', 'PRORATED')",
            name="ck_thr_records_calculation_basis",
        ),
        UniqueConstraint(
            "employee_id", "thr_year", "religious_holiday",
            name="uq_thr_records_employee_year_holiday",
        ),
        Index("idx_thr_records_employee", "employee_id"),
        Index("idx_thr_records_year", "thr_year"),
    )


class ReimbursementType(Base, TimestampMixin):
    """Types of reimbursements available in a company."""

    __tablename__ = "reimbursement_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    max_amount = Column(Numeric(15, 2), nullable=True)
    is_taxable = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    reimbursements = relationship("Reimbursement", backref="reimbursement_type")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_reimbursement_types_company_code"),
    )


class Reimbursement(Base, TimestampMixin):
    """Employee reimbursement claims."""

    __tablename__ = "reimbursements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    reimbursement_type_id = Column(Integer, ForeignKey("reimbursement_types.id"), nullable=False)
    claim_amount = Column(Numeric(15, 2), nullable=False)
    approved_amount = Column(Numeric(15, 2), nullable=True)
    claim_date = Column(Date, nullable=False)
    expense_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    receipt_path = Column(String(500), nullable=True)
    approval_status = Column(String(20), nullable=False, default="PENDING")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=True)
    is_processed = Column(Boolean, default=False)

    __table_args__ = (
        CheckConstraint(
            "claim_amount > 0",
            name="ck_reimbursements_claim_amount_positive",
        ),
        CheckConstraint(
            "approval_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_reimbursements_approval_status",
        ),
        Index("idx_reimbursements_employee", "employee_id"),
    )
