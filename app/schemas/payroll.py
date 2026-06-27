"""
Pydantic schemas for Payroll processing API contracts.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, PaginatedResponse


# --- PayrollRun Schemas ---


class PayrollRunCreate(BaseSchema):
    """Request schema for creating a new payroll run."""

    company_id: int
    payroll_period: str = Field(..., description="Payroll period in YYYY-MM format")
    period_start_date: date
    period_end_date: date
    payroll_method: Optional[Literal["GROSS", "GROSS_UP", "NETT"]] = None
    tax_method: Literal["PASAL_17", "TER"] = "PASAL_17"
    notes: Optional[str] = None

    @field_validator("payroll_period")
    @classmethod
    def validate_payroll_period(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", v):
            raise ValueError("payroll_period must be in YYYY-MM format")
        return v

    @field_validator("period_end_date")
    @classmethod
    def validate_period_dates(cls, v: date, info) -> date:
        start = info.data.get("period_start_date")
        if start and v < start:
            raise ValueError("period_end_date must be after period_start_date")
        return v


class PayrollRunResponse(BaseSchema):
    """Response schema for a payroll run."""

    id: int
    company_id: int
    payroll_period: str
    period_start_date: date
    period_end_date: date
    payroll_method: str
    tax_method: str
    status: str
    total_employees: int
    total_gross: Decimal
    total_deductions: Decimal
    total_tax: Decimal
    total_net: Decimal
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approval_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PayrollRunListResponse(PaginatedResponse[PayrollRunResponse]):
    """Paginated list of payroll runs."""

    pass


# --- Payslip Schemas ---


class PayslipLineResponse(BaseSchema):
    """Response schema for a payslip line item."""

    id: int
    payslip_id: int
    line_type: str
    category: Optional[str] = None
    description: str
    amount: Decimal
    sort_order: int


class PayslipResponse(BaseSchema):
    """Response schema for a payslip."""

    id: int
    payroll_run_id: int
    employee_id: int
    payslip_number: str
    basic_salary: Decimal
    total_allowances: Decimal
    overtime_amount: Decimal
    bonus_amount: Decimal
    gross_salary: Decimal
    bpjs_kes_employee: Decimal
    bpjs_jht_employee: Decimal
    bpjs_jp_employee: Decimal
    pph21_tax: Decimal
    kasbon_deduction: Decimal
    other_deductions: Decimal
    total_deductions: Decimal
    net_salary: Decimal
    tax_allowance: Decimal
    working_days: int
    overtime_hours: Decimal
    late_minutes: int
    sick_days: int
    leave_days: int
    allowances_detail: Optional[str] = None
    deductions_detail: Optional[str] = None
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class PayslipDetailResponse(PayslipResponse):
    """Payslip response with detailed line items."""

    lines: List[PayslipLineResponse] = []
