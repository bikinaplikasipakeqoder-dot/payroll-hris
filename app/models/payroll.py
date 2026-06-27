"""
Payroll processing models for the Payroll & HRIS system.

Tables:
- payroll_runs: Payroll batch processing runs
- payslips: Individual employee payslips per payroll run
- payslip_lines: Detailed line items for each payslip
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class PayrollRun(Base, TimestampMixin):
    """Payroll batch processing runs for a company."""

    __tablename__ = "payroll_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    payroll_period = Column(String(20), nullable=False)
    period_start_date = Column(Date, nullable=False)
    period_end_date = Column(Date, nullable=False)
    payroll_method = Column(String(20), nullable=False, default="GROSS")
    tax_method = Column(String(20), nullable=False, default="PASAL_17")
    status = Column(String(20), nullable=False, default="DRAFT")
    total_employees = Column(Integer, default=0)
    total_gross = Column(Numeric(18, 2), default=0)
    total_deductions = Column(Numeric(18, 2), default=0)
    total_tax = Column(Numeric(18, 2), default=0)
    total_net = Column(Numeric(18, 2), default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    payslips = relationship("Payslip", backref="payroll_run")

    __table_args__ = (
        CheckConstraint(
            "payroll_method IN ('GROSS', 'GROSS_UP', 'NETT')",
            name="ck_payroll_runs_payroll_method",
        ),
        CheckConstraint(
            "tax_method IN ('PASAL_17', 'TER')",
            name="ck_payroll_runs_tax_method",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'PROCESSING', 'COMPLETED', 'APPROVED', 'PAID')",
            name="ck_payroll_runs_status",
        ),
        UniqueConstraint("company_id", "payroll_period", name="uq_payroll_runs_company_period"),
        Index("idx_payroll_runs_period", "company_id", "payroll_period"),
        Index("idx_payroll_runs_status", "status"),
    )


class Payslip(Base, TimestampMixin):
    """Individual employee payslips per payroll run."""

    __tablename__ = "payslips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    payslip_number = Column(String(50), unique=True, nullable=False)
    basic_salary = Column(Numeric(15, 2), nullable=False, default=0)
    total_allowances = Column(Numeric(15, 2), nullable=False, default=0)
    overtime_amount = Column(Numeric(15, 2), nullable=False, default=0)
    bonus_amount = Column(Numeric(15, 2), nullable=False, default=0)
    gross_salary = Column(Numeric(15, 2), nullable=False, default=0)
    bpjs_kes_employee = Column(Numeric(15, 2), nullable=False, default=0)
    bpjs_jht_employee = Column(Numeric(15, 2), nullable=False, default=0)
    bpjs_jp_employee = Column(Numeric(15, 2), nullable=False, default=0)
    pph21_tax = Column(Numeric(15, 2), nullable=False, default=0)
    kasbon_deduction = Column(Numeric(15, 2), nullable=False, default=0)
    other_deductions = Column(Numeric(15, 2), nullable=False, default=0)
    total_deductions = Column(Numeric(15, 2), nullable=False, default=0)
    net_salary = Column(Numeric(15, 2), nullable=False, default=0)
    tax_allowance = Column(Numeric(15, 2), nullable=False, default=0)
    working_days = Column(Integer, default=0)
    overtime_hours = Column(Numeric(5, 2), default=0)
    late_minutes = Column(Integer, default=0)
    sick_days = Column(Integer, default=0)
    leave_days = Column(Integer, default=0)
    allowances_detail = Column(Text, nullable=True)
    deductions_detail = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)

    # Relationships
    lines = relationship("PayslipLine", backref="payslip")

    __table_args__ = (
        UniqueConstraint("payroll_run_id", "employee_id", name="uq_payslips_run_employee"),
        Index("idx_payslips_employee", "employee_id"),
    )


class PayslipLine(Base, TimestampMixin):
    """Detailed line items for each payslip."""

    __tablename__ = "payslip_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payslip_id = Column(Integer, ForeignKey("payslips.id"), nullable=False)
    line_type = Column(String(20), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    sort_order = Column(Integer, default=0)

    __table_args__ = (
        CheckConstraint(
            "line_type IN ('EARNING', 'DEDUCTION', 'TAX', 'BPJS', 'NET')",
            name="ck_payslip_lines_line_type",
        ),
    )


class PayslipTemplate(Base, TimestampMixin):
    """Admin-editable HTML templates for payslip PDF generation."""

    __tablename__ = "payslip_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    template_name = Column(String(100), nullable=False)
    html_content = Column(Text, nullable=False)
    css_content = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_payslip_templates_company_default", "company_id", "is_default"),
    )


class PayslipRecord(Base, TimestampMixin):
    """Metadata for generated payslip PDF files."""

    __tablename__ = "payslip_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payslip_id = Column(Integer, ForeignKey("payslips.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    generated_at = Column(DateTime, nullable=True)
    generated_by = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'COMPLETED', 'FAILED')",
            name="ck_payslip_records_status",
        ),
        Index("idx_payslip_records_lookup", "company_id", "employee_id", "year", "month"),
        Index("idx_payslip_records_payslip", "payslip_id"),
    )


class PayslipGenerationJob(Base, TimestampMixin):
    """Tracks bulk payslip PDF generation jobs."""

    __tablename__ = "payslip_generation_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), unique=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=False)
    total_count = Column(Integer, nullable=False, default=0)
    completed_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="QUEUED")
    result_file_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED')",
            name="ck_payslip_generation_jobs_status",
        ),
        Index("idx_payslip_jobs_company_status", "company_id", "status"),
        Index("idx_payslip_jobs_job_id", "job_id"),
    )
