"""
Pydantic schemas for employee loan / cash advance (kasbon) management.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from app.schemas.base import BaseSchema


class KasbonInstallmentResponse(BaseSchema):
    """Response schema for a single kasbon installment."""

    id: int
    installment_number: int
    amount: Decimal
    due_date: date
    is_paid: bool
    paid_date: Optional[date] = None
    payroll_run_id: Optional[int] = None


class KasbonCreate(BaseSchema):
    """Request schema for creating a kasbon request."""

    employee_id: int
    kasbon_number: str
    principal_amount: Decimal
    purpose: str
    request_date: date
    number_of_installments: int
    installment_amount: Decimal
    notes: Optional[str] = None


class KasbonUpdate(BaseSchema):
    """Request schema for updating a kasbon request."""

    principal_amount: Optional[Decimal] = None
    purpose: Optional[str] = None
    request_date: Optional[date] = None
    number_of_installments: Optional[int] = None
    installment_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[int] = None
    approval_date: Optional[date] = None
    disbursement_date: Optional[date] = None


class KasbonStatusUpdate(BaseSchema):
    """Request schema for changing kasbon status (approve/reject/disburse)."""

    status: str
    approved_by: Optional[int] = None


class KasbonResponse(BaseSchema):
    """Response schema for a kasbon request."""

    id: int
    employee_id: int
    employee_name: str
    kasbon_number: str
    principal_amount: Decimal
    purpose: str
    request_date: date
    approval_date: Optional[date] = None
    disbursement_date: Optional[date] = None
    number_of_installments: int
    installment_amount: Decimal
    status: str
    approved_by: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    installments: List[KasbonInstallmentResponse] = []
    total_paid: Decimal = Decimal("0")
    remaining_balance: Decimal = Decimal("0")
