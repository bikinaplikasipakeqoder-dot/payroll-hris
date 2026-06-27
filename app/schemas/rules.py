"""
Pydantic schemas for the Rules Engine API.
"""

from typing import Optional, Literal
from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from app.schemas.base import BaseSchema


class RuleCategoryResponse(BaseSchema):
    """Response schema for a rule category."""

    id: int
    category_code: str
    category_name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class RuleConfigurationCreate(BaseSchema):
    """Request schema for creating a rule."""

    company_id: int
    category_id: int
    rule_code: str = Field(..., max_length=100)
    rule_name: str = Field(..., max_length=255)
    rule_type: Literal["FORMULA", "CONSTANT", "BRACKET", "LOOKUP_TABLE"]
    formula: Optional[str] = None
    value: Optional[Decimal] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    effective_date: date
    expiry_date: Optional[date] = None
    priority: int = 0
    is_active: bool = True
    description: Optional[str] = None


class RuleConfigurationUpdate(BaseSchema):
    """Request schema for updating a rule (partial)."""

    category_id: Optional[int] = None
    rule_code: Optional[str] = Field(None, max_length=100)
    rule_name: Optional[str] = Field(None, max_length=255)
    rule_type: Optional[Literal["FORMULA", "CONSTANT", "BRACKET", "LOOKUP_TABLE"]] = None
    formula: Optional[str] = None
    value: Optional[Decimal] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class RuleConfigurationResponse(BaseSchema):
    """Response schema for a rule configuration."""

    id: int
    company_id: int
    category_id: int
    category_code: str
    category_name: str
    rule_code: str
    rule_name: str
    rule_type: str
    formula: Optional[str] = None
    value: Optional[Decimal] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    effective_date: date
    expiry_date: Optional[date] = None
    priority: int
    is_active: bool
    description: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class RuleVariableResponse(BaseSchema):
    """Response schema for a rule variable."""

    id: int
    variable_code: str
    variable_name: str
    variable_type: str
    source_table: Optional[str] = None
    source_field: Optional[str] = None
    description: Optional[str] = None
    is_active: bool


class RuleAuditLogResponse(BaseSchema):
    """Response schema for rule audit log entries."""

    id: int
    rule_id: int
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_by: int
    changed_by_name: Optional[str] = None
    changed_at: datetime
    reason: Optional[str] = None


class RuleResetRequest(BaseSchema):
    """Request schema for resetting rules in a category."""

    company_id: int
    category_id: int
    reason: Optional[str] = None
