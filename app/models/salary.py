"""
Salary structure and compensation models for the Payroll & HRIS system.

Tables:
- grades: Employee grade/level definitions
- grade_salary_matrix: Salary ranges per grade with effective dates
- allowance_types: Types of allowances (fixed, percentage, formula)
- employee_allowances: Individual employee allowance assignments
- deduction_types: Types of deductions
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Grade(Base, TimestampMixin):
    """Employee grade/level definitions."""

    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    grade_name = Column(String(100), nullable=False)
    grade_code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    salary_matrix = relationship("GradeSalaryMatrix", backref="grade")

    __table_args__ = (
        UniqueConstraint("company_id", "grade_code", name="uq_grades_company_code"),
    )


class GradeSalaryMatrix(Base, TimestampMixin):
    """Salary ranges per grade with effective dates."""

    __tablename__ = "grade_salary_matrix"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grade_id = Column(Integer, ForeignKey("grades.id"), nullable=False)
    basic_salary_min = Column(Numeric(15, 2), nullable=False)
    basic_salary_max = Column(Numeric(15, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "basic_salary_min <= basic_salary_max",
            name="ck_grade_salary_matrix_min_max",
        ),
    )


class AllowanceType(Base, TimestampMixin):
    """Types of allowances (fixed, percentage, formula-based)."""

    __tablename__ = "allowance_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    calculation_type = Column(String(20), nullable=False, default="FIXED")
    amount_basis = Column(String(20), nullable=False, default="UNIVERSAL")
    is_taxable = Column(Boolean, default=True)
    is_bpjs_base = Column(Boolean, default=True)
    formula_template = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "calculation_type IN ('FIXED', 'PERCENTAGE', 'FORMULA')",
            name="ck_allowance_types_calculation_type",
        ),
        CheckConstraint(
            "amount_basis IN ('UNIVERSAL', 'GRADE', 'POSITION', 'DEPARTMENT', 'INDIVIDUAL')",
            name="ck_allowance_types_amount_basis",
        ),
        UniqueConstraint("company_id", "code", name="uq_allowance_types_company_code"),
    )


class EmployeeAllowance(Base, TimestampMixin):
    """Individual employee allowance assignments."""

    __tablename__ = "employee_allowances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    allowance_type_id = Column(Integer, ForeignKey("allowance_types.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    allowance_type = relationship("AllowanceType", backref="employee_allowances")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_employee_allowances_amount"),
        UniqueConstraint(
            "employee_id", "allowance_type_id", "effective_date",
            name="uq_employee_allowances_emp_type_date",
        ),
    )


class AllowanceGradeMatrix(Base, TimestampMixin):
    """Allowance amounts per grade."""

    __tablename__ = "allowance_grade_matrix"

    id = Column(Integer, primary_key=True, autoincrement=True)
    allowance_type_id = Column(Integer, ForeignKey("allowance_types.id"), nullable=False)
    grade_id = Column(Integer, ForeignKey("grades.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_allowance_grade_matrix_amount"),
        UniqueConstraint(
            "allowance_type_id", "grade_id", "effective_date",
            name="uq_allowance_grade_matrix_type_grade_date",
        ),
    )


class AllowancePositionMatrix(Base, TimestampMixin):
    """Allowance amounts per position."""

    __tablename__ = "allowance_position_matrix"

    id = Column(Integer, primary_key=True, autoincrement=True)
    allowance_type_id = Column(Integer, ForeignKey("allowance_types.id"), nullable=False)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_allowance_position_matrix_amount"),
        UniqueConstraint(
            "allowance_type_id", "position_id", "effective_date",
            name="uq_allowance_position_matrix_type_position_date",
        ),
    )


class AllowanceDepartmentMatrix(Base, TimestampMixin):
    """Allowance amounts per department."""

    __tablename__ = "allowance_department_matrix"

    id = Column(Integer, primary_key=True, autoincrement=True)
    allowance_type_id = Column(Integer, ForeignKey("allowance_types.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_allowance_department_matrix_amount"),
        UniqueConstraint(
            "allowance_type_id", "department_id", "effective_date",
            name="uq_allowance_department_matrix_type_department_date",
        ),
    )


class DeductionType(Base, TimestampMixin):
    """Types of deductions."""

    __tablename__ = "deduction_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    calculation_type = Column(String(20), nullable=False, default="FIXED")
    is_recurring = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "calculation_type IN ('FIXED', 'PERCENTAGE', 'FORMULA')",
            name="ck_deduction_types_calculation_type",
        ),
        UniqueConstraint("company_id", "code", name="uq_deduction_types_company_code"),
    )


class EmployeeSalaryHistory(Base, TimestampMixin):
    """Historical base salary records per employee with effective dates.

    Implements the Effective Date pattern: do not mutate old salary records.
    When a salary changes, create a new record with effective_date = start date.
    Payroll calculation selects the most recent record where effective_date <= period end.
    """

    __tablename__ = "employee_salary_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    base_salary = Column(Numeric(15, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("base_salary >= 0", name="ck_employee_salary_history_amount"),
        CheckConstraint(
            "end_date IS NULL OR end_date >= effective_date",
            name="ck_employee_salary_history_dates",
        ),
        UniqueConstraint(
            "employee_id", "effective_date",
            name="uq_employee_salary_history_emp_date",
        ),
        Index("idx_employee_salary_history_employee", "employee_id"),
        Index("idx_employee_salary_history_effective", "employee_id", "effective_date"),
    )
