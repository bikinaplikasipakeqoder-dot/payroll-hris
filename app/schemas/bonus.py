"""
Pydantic schemas for bonus and reimbursement management.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.schemas.base import BaseSchema


# ─── Bonus Type ──────────────────────────────────────────────────────────────


class BonusTypeCreate(BaseSchema):
    """Request schema for creating a bonus type."""

    company_id: int
    name: str
    code: str
    is_taxable: bool = True
    is_active: bool = True


class BonusTypeUpdate(BaseSchema):
    """Request schema for updating a bonus type."""

    name: Optional[str] = None
    code: Optional[str] = None
    is_taxable: Optional[bool] = None
    is_active: Optional[bool] = None


class BonusTypeResponse(BaseSchema):
    """Response schema for a bonus type."""

    id: int
    company_id: int
    name: str
    code: str
    is_taxable: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── Bonus ───────────────────────────────────────────────────────────────────


class BonusCreate(BaseSchema):
    """Request schema for creating a bonus record."""

    employee_id: int
    bonus_type_id: int
    amount: Decimal
    bonus_date: date
    description: Optional[str] = None


class BonusUpdate(BaseSchema):
    """Request schema for updating a bonus record."""

    bonus_type_id: Optional[int] = None
    amount: Optional[Decimal] = None
    bonus_date: Optional[date] = None
    description: Optional[str] = None
    approval_status: Optional[str] = None


class BonusResponse(BaseSchema):
    """Response schema for a bonus record."""

    id: int
    employee_id: int
    employee_name: str
    bonus_type_id: int
    bonus_type_name: str
    amount: Decimal
    bonus_date: date
    description: Optional[str] = None
    approval_status: str
    approved_by: Optional[int] = None
    approval_date: Optional[datetime] = None
    payroll_run_id: Optional[int] = None
    is_processed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── THR ─────────────────────────────────────────────────────────────────────


class THRCreate(BaseSchema):
    """Request schema for creating a THR record."""

    employee_id: int
    thr_year: int
    religious_holiday: str
    amount: Decimal
    thr_date: date
    calculation_basis: str = "BASE_SALARY"
    tenure_months: int = 0
    description: Optional[str] = None


class THRUpdate(BaseSchema):
    """Request schema for updating a THR record."""

    amount: Optional[Decimal] = None
    thr_date: Optional[date] = None
    status: Optional[str] = None
    description: Optional[str] = None


class THRCalculateRequest(BaseSchema):
    """Request schema for bulk THR calculation."""

    company_id: int
    thr_year: int
    religious_holiday: str
    reference_date: date


class THRResponse(BaseSchema):
    """Response schema for a THR record."""

    id: int
    company_id: int
    employee_id: int
    employee_name: str
    employee_religion: Optional[str]
    thr_year: int
    religious_holiday: str
    amount: Decimal
    thr_date: date
    calculation_basis: str
    tenure_months: int
    status: str
    description: Optional[str] = None
    payroll_run_id: Optional[int] = None
    is_processed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
