"""
Pydantic schemas for BPJS configuration API contracts.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional

from app.schemas.base import BaseSchema


class BpjsSettingResponse(BaseSchema):
    """Response schema for BPJS settings."""

    id: int
    company_id: int
    bpjs_type: str
    employee_rate: Decimal
    employer_rate: Decimal
    max_salary_base: Optional[Decimal] = None
    regulation_year: int
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class BpjsSettingCreate(BaseSchema):
    """Request schema for creating BPJS settings."""

    company_id: int
    bpjs_type: str
    employee_rate: Decimal
    employer_rate: Decimal
    max_salary_base: Optional[Decimal] = None
    regulation_year: int
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool = True


class BpjsSettingUpdate(BaseSchema):
    """Request schema for updating BPJS settings."""

    employee_rate: Optional[Decimal] = None
    employer_rate: Optional[Decimal] = None
    max_salary_base: Optional[Decimal] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
