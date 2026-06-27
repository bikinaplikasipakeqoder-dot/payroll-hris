"""
Pydantic schemas for Company Entities and UMP settings.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema, PaginatedResponse


class EntityCreate(BaseSchema):
    """Request schema for creating a company entity/branch."""

    company_id: int
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field("Indonesia", max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)


class EntityUpdate(BaseSchema):
    """Request schema for updating a company entity (partial)."""

    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class EntityResponse(BaseSchema):
    """Response schema for a company entity."""

    id: int
    company_id: int
    code: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class EntityListResponse(PaginatedResponse[EntityResponse]):
    """Paginated list of entities."""

    pass


class UmpSettingCreate(BaseSchema):
    """Request schema for creating a UMP setting."""

    company_id: int
    province: str = Field(..., max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    amount: Decimal = Field(..., ge=0)
    effective_date: date


class UmpSettingUpdate(BaseSchema):
    """Request schema for updating a UMP setting (partial)."""

    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    amount: Optional[Decimal] = Field(None, ge=0)
    effective_date: Optional[date] = None
    is_active: Optional[bool] = None


class UmpSettingResponse(BaseSchema):
    """Response schema for a UMP setting."""

    id: int
    company_id: int
    province: str
    city: Optional[str] = None
    amount: Decimal
    effective_date: date
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class UmpSettingListResponse(PaginatedResponse[UmpSettingResponse]):
    """Paginated list of UMP settings."""

    pass
