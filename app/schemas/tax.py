"""
Pydantic schemas for Tax configuration API contracts.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional

from app.schemas.base import BaseSchema


class TaxSettingResponse(BaseSchema):
    """Response schema for company tax settings."""

    id: int
    company_id: int
    tax_calculation_method: str
    payroll_method: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class TaxSettingUpdate(BaseSchema):
    """Request schema for updating tax settings."""

    tax_calculation_method: Optional[str] = None
    payroll_method: Optional[str] = None
    is_active: Optional[bool] = None


class TaxSettingCreate(BaseSchema):
    """Request schema for creating tax settings."""

    company_id: int
    tax_calculation_method: str = "PASAL_17"
    payroll_method: str = "GROSS"
    is_active: bool = True


class PtkpValueCreate(BaseSchema):
    """Request schema for creating a PTKP value."""

    company_id: int
    ptkp_code: str
    description: str
    annual_amount: Decimal
    monthly_amount: Decimal
    regulation_year: int
    regulation_reference: Optional[str] = None
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool = True


class PtkpValueUpdate(BaseSchema):
    """Request schema for updating a PTKP value."""

    ptkp_code: Optional[str] = None
    description: Optional[str] = None
    annual_amount: Optional[Decimal] = None
    monthly_amount: Optional[Decimal] = None
    regulation_year: Optional[int] = None
    regulation_reference: Optional[str] = None
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class TaxBracketCreate(BaseSchema):
    """Request schema for creating a Pasal 17 tax bracket."""

    company_id: int
    bracket_order: int
    income_range_min: Decimal
    income_range_max: Optional[Decimal] = None
    tax_rate: Decimal
    regulation_year: int
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool = True


class TaxBracketUpdate(BaseSchema):
    """Request schema for updating a Pasal 17 tax bracket."""

    bracket_order: Optional[int] = None
    income_range_min: Optional[Decimal] = None
    income_range_max: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    regulation_year: Optional[int] = None
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class TerBracketCreate(BaseSchema):
    """Request schema for creating a TER bracket."""

    company_id: int
    category: str
    income_range_min: Decimal
    income_range_max: Optional[Decimal] = None
    ter_rate: Decimal
    regulation_year: int
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool = True


class TerBracketUpdate(BaseSchema):
    """Request schema for updating a TER bracket."""

    category: Optional[str] = None
    income_range_min: Optional[Decimal] = None
    income_range_max: Optional[Decimal] = None
    ter_rate: Optional[Decimal] = None
    regulation_year: Optional[int] = None
    effective_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class PtkpValueResponse(BaseSchema):
    """Response schema for PTKP threshold values."""

    id: int
    company_id: int
    ptkp_code: str
    description: str
    annual_amount: Decimal
    monthly_amount: Decimal
    regulation_year: int
    regulation_reference: Optional[str] = None
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class TaxBracketResponse(BaseSchema):
    """Response schema for PPh Pasal 17 progressive tax brackets."""

    id: int
    company_id: int
    bracket_order: int
    income_range_min: Decimal
    income_range_max: Optional[Decimal] = None
    tax_rate: Decimal
    regulation_year: int
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class TerBracketResponse(BaseSchema):
    """Response schema for TER (Tarif Efektif Rata-rata) brackets."""

    id: int
    company_id: int
    category: str
    income_range_min: Decimal
    income_range_max: Optional[Decimal] = None
    ter_rate: Decimal
    regulation_year: int
    effective_date: date
    end_date: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
