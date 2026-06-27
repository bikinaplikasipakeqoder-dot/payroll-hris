"""
Employee and organizational structure models for the Payroll & HRIS system.

Tables:
- departments: Organizational departments with hierarchy support
- positions: Job positions/titles
- employment_statuses: Employment status types (permanent, contract, etc.)
- employees: Core employee master data
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    """Organizational departments with hierarchy support."""

    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    parent_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    # Self-referential relationship for department hierarchy
    parent = relationship("Department", remote_side="Department.id", backref="children")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_departments_company_code"),
    )


class Position(Base, TimestampMixin):
    """Job positions/titles within a company."""

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_positions_company_code"),
    )


class EmploymentStatus(Base, TimestampMixin):
    """Employment status types (e.g., permanent, contract, probation)."""

    __tablename__ = "employment_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    is_permanent = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_employment_statuses_company_code"),
    )


class Employee(Base, TimestampMixin):
    """Core employee master data."""

    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    employee_code = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    personal_id_number = Column(String(50), nullable=True)
    npwp = Column(String(50), nullable=True)
    ptkp_status = Column(String(10), nullable=False, default="TK/0")
    religion = Column(String(30), nullable=True, default="Islam")
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address_street = Column(Text, nullable=True)
    address_city = Column(String(100), nullable=True)
    address_province = Column(String(100), nullable=True)
    address_postal_code = Column(String(10), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    grade_id = Column(Integer, ForeignKey("grades.id"), nullable=True)
    employment_status_id = Column(
        Integer, ForeignKey("employment_statuses.id"), nullable=True
    )
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    date_joined = Column(Date, nullable=False)
    date_left = Column(Date, nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    bank_account_holder_name = Column(String(255), nullable=True)
    base_salary = Column(Numeric(15, 2), nullable=True)
    bpjs_kesehatan_number = Column(String(30), nullable=True)
    bpjs_ketenagakerjaan_number = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    department = relationship("Department", backref="employees")
    position = relationship("Position", backref="employees")
    employment_status = relationship("EmploymentStatus", backref="employees")
    entity = relationship("Entity", backref="employees")
    employee_allowances = relationship("EmployeeAllowance", backref="employee", lazy="select")

    __table_args__ = (
        CheckConstraint(
            "gender IN ('M', 'F')",
            name="ck_employees_gender",
        ),
        CheckConstraint(
            "ptkp_status IN ('TK/0','TK/1','TK/2','TK/3','K/0','K/1','K/2','K/3')",
            name="ck_employees_ptkp_status",
        ),
        CheckConstraint(
            "religion IN ('Islam','Protestan','Katolik','Hindu','Buddha','Konghucu')",
            name="ck_employees_religion",
        ),
        Index("idx_employees_company_active", "company_id", "is_active"),
        Index("idx_employees_department", "department_id"),
        Index("idx_employees_entity", "entity_id"),
        Index("idx_employees_ptkp", "ptkp_status"),
    )
