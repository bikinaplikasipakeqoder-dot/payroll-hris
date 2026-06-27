"""
Pydantic schemas for salary structure and compensation entities.
"""

from typing import Optional
from datetime import date, datetime
from decimal import Decimal

from app.schemas.base import BaseSchema


class AllowanceTypeCreate(BaseSchema):
    """Request schema for creating an allowance type."""

    company_id: int
    name: str
    code: str
    description: Optional[str] = None
    calculation_type: str = "FIXED"
    amount_basis: str = "UNIVERSAL"
    is_taxable: bool = True
    is_bpjs_base: bool = True
    formula_template: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class AllowanceTypeUpdate(BaseSchema):
    """Request schema for updating an allowance type."""

    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    calculation_type: Optional[str] = None
    amount_basis: Optional[str] = None
    is_taxable: Optional[bool] = None
    is_bpjs_base: Optional[bool] = None
    formula_template: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class AllowanceTypeResponse(BaseSchema):
    """Response schema for allowance types."""

    id: int
    company_id: int
    name: str
    code: str
    description: Optional[str] = None
    calculation_type: str
    amount_basis: str
    is_taxable: bool
    is_bpjs_base: bool
    formula_template: Optional[str] = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class EmployeeAllowanceCreate(BaseSchema):
    """Request schema for creating an employee allowance assignment."""

    allowance_type_id: int
    amount: Decimal
    effective_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: bool = True


class EmployeeAllowanceUpdate(BaseSchema):
    """Request schema for updating an employee allowance assignment."""

    allowance_type_id: Optional[int] = None
    amount: Optional[Decimal] = None
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeAllowanceResponse(BaseSchema):
    """Response schema for employee allowance assignments."""

    id: int
    employee_id: int
    allowance_type_id: int
    allowance_type_name: str
    allowance_type_code: str
    amount: Decimal
    effective_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class AllowanceMatrixCreate(BaseSchema):
    """Request schema for creating an allowance matrix entry."""

    allowance_type_id: int
    entity_id: int
    amount: Decimal
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool = True


class AllowanceMatrixUpdate(BaseSchema):
    """Request schema for updating an allowance matrix entry."""

    entity_id: Optional[int] = None
    amount: Optional[Decimal] = None
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class AllowanceMatrixResponse(BaseSchema):
    """Response schema for allowance matrix entries."""

    id: int
    allowance_type_id: int
    entity_id: int
    entity_name: str
    amount: Decimal
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class DeductionTypeCreate(BaseSchema):
    """Request schema for creating a deduction type."""

    company_id: int
    name: str
    code: str
    description: Optional[str] = None
    calculation_type: str = "FIXED"
    is_recurring: bool = False
    is_active: bool = True


class DeductionTypeUpdate(BaseSchema):
    """Request schema for updating a deduction type."""

    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    calculation_type: Optional[str] = None
    is_recurring: Optional[bool] = None
    is_active: Optional[bool] = None


class DeductionTypeResponse(BaseSchema):
    """Response schema for deduction types."""

    id: int
    company_id: int
    name: str
    code: str
    description: Optional[str] = None
    calculation_type: str
    is_recurring: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
