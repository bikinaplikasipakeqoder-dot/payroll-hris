"""
Leave management models for the Payroll & HRIS system.

Tables:
- leave_types: Types of leave available in a company
- employee_leave_balances: Annual leave balance tracking per employee
- leave_requests: Employee leave request submissions and approvals
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class LeaveType(Base, TimestampMixin):
    """Types of leave available in a company."""

    __tablename__ = "leave_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    default_annual_entitlement = Column(Integer, nullable=False, default=12)
    is_paid = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    balances = relationship("EmployeeLeaveBalance", backref="leave_type")
    requests = relationship("LeaveRequest", backref="leave_type")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_leave_types_company_code"),
    )


class EmployeeLeaveBalance(Base, TimestampMixin):
    """Annual leave balance tracking per employee and leave type."""

    __tablename__ = "employee_leave_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    year = Column(Integer, nullable=False)
    opening_balance = Column(Integer, nullable=False, default=0)
    entitlement = Column(Integer, nullable=False)
    used = Column(Integer, nullable=False, default=0)
    carried_forward = Column(Integer, nullable=False, default=0)
    closing_balance = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint(
            "employee_id", "leave_type_id", "year",
            name="uq_employee_leave_balances_emp_type_year",
        ),
    )


class LeaveRequest(Base, TimestampMixin):
    """Employee leave request submissions and approvals."""

    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    reason = Column(Text, nullable=True)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')",
            name="ck_leave_requests_status",
        ),
        CheckConstraint(
            "start_date <= end_date",
            name="ck_leave_requests_date_range",
        ),
        CheckConstraint(
            "days_requested > 0",
            name="ck_leave_requests_days_positive",
        ),
    )
