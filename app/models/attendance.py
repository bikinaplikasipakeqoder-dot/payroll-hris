"""
Attendance and overtime models for the Payroll & HRIS system.

Tables:
- shifts: Work shift definitions
- employee_shift_assignments: Assignment of shifts to employees
- attendance_records: Daily attendance tracking
- overtime_records: Overtime work records
- overtime_settings: Company-level overtime configuration
- attendance_working_days_configs: Monthly working days configuration per company
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Shift(Base, TimestampMixin):
    """Work shift definitions for a company."""

    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    break_duration_minutes = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)

    # Relationships
    assignments = relationship("EmployeeShiftAssignment", backref="shift")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_shifts_company_code"),
    )


class EmployeeShiftAssignment(Base, TimestampMixin):
    """Assignment of shifts to employees with effective date ranges."""

    __tablename__ = "employee_shift_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)


class AttendanceRecord(Base, TimestampMixin):
    """Daily attendance tracking for employees."""

    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    attendance_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    check_in_time = Column(String(8), nullable=True)
    check_out_time = Column(String(8), nullable=True)
    is_late = Column(Boolean, default=False)
    late_minutes = Column(Integer, default=0)
    hours_worked = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('PRESENT', 'ABSENT', 'LEAVE', 'SICK', 'PERMITTED')",
            name="ck_attendance_records_status",
        ),
        UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
        Index("idx_attendance_employee_date", "employee_id", "attendance_date"),
        Index("idx_attendance_date_status", "attendance_date", "status"),
    )


class OvertimeRecord(Base, TimestampMixin):
    """Overtime work records for employees."""

    __tablename__ = "overtime_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    overtime_date = Column(Date, nullable=False)
    overtime_type = Column(String(20), nullable=False)
    hours = Column(Numeric(5, 2), nullable=False)
    multiplier = Column(Numeric(3, 2), nullable=False, default=1.5)
    calculated_amount = Column(Numeric(15, 2), nullable=True)
    approval_status = Column(String(20), nullable=False, default="PENDING")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "overtime_type IN ('WEEKDAY', 'WEEKEND', 'HOLIDAY')",
            name="ck_overtime_records_type",
        ),
        CheckConstraint(
            "approval_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="ck_overtime_records_approval_status",
        ),
        Index("idx_overtime_employee_date", "employee_id", "overtime_date"),
    )


class OvertimeSetting(Base, TimestampMixin):
    """Company-level overtime configuration and multiplier settings."""

    __tablename__ = "overtime_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, unique=True)
    work_week_type = Column(String(10), nullable=False, default="5_DAY")
    weekday_first_hour_multiplier = Column(Numeric(3, 2), nullable=False, default=1.5)
    weekday_subsequent_multiplier = Column(Numeric(3, 2), nullable=False, default=2.0)
    weekend_first_hour_multiplier = Column(Numeric(3, 2), nullable=False, default=2.0)
    weekend_subsequent_multiplier = Column(Numeric(3, 2), nullable=False, default=3.0)
    late_penalty_per_minute = Column(Numeric(10, 2), nullable=True, default=0)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "work_week_type IN ('5_DAY', '6_DAY')",
            name="ck_overtime_settings_work_week_type",
        ),
    )


class AttendanceWorkingDaysConfig(Base, TimestampMixin):
    """Monthly working days configuration per company.

    Allows admins to override the default weekday-based calculation
    to account for government-declared holidays.
    """

    __tablename__ = "attendance_working_days_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    working_days = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("month >= 1 AND month <= 12", name="ck_awdc_month"),
        CheckConstraint("working_days >= 0 AND working_days <= 31", name="ck_awdc_working_days"),
        UniqueConstraint("company_id", "year", "month", name="uq_awdc_company_year_month"),
    )
