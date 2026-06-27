"""
Pydantic schemas for AI module endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import Field

from app.schemas.base import BaseSchema


# --- Settings Schemas ---

class AiSettingCreate(BaseSchema):
    """Request schema for creating AI settings."""
    company_id: int
    provider_name: str = Field(..., max_length=100)
    api_key: Optional[str] = None
    api_host: Optional[str] = Field(None, max_length=500)
    model_name: str = Field(..., max_length=100)
    system_prompt: Optional[str] = None
    temperature: Optional[Decimal] = Field(default=Decimal("0.70"), ge=0, le=2)
    max_tokens: Optional[int] = Field(default=2048, ge=1, le=128000)
    timeout_seconds: Optional[int] = Field(default=9, ge=1, le=60)
    is_active: bool = True


class AiSettingUpdate(BaseSchema):
    """Request schema for updating AI settings (all optional)."""
    provider_name: Optional[str] = Field(None, max_length=100)
    api_key: Optional[str] = None
    api_host: Optional[str] = Field(None, max_length=500)
    model_name: Optional[str] = Field(None, max_length=100)
    system_prompt: Optional[str] = None
    temperature: Optional[Decimal] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=60)
    is_active: Optional[bool] = None


class AiSettingResponse(BaseSchema):
    """Response schema for AI settings (API key masked)."""
    id: int
    company_id: int
    provider_name: str
    api_key_masked: Optional[str] = None
    api_host: Optional[str] = None
    model_name: str
    system_prompt: Optional[str] = None
    temperature: Optional[Decimal] = None
    max_tokens: Optional[int] = None
    timeout_seconds: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Chat Schemas ---

class AiChatRequest(BaseSchema):
    """Request schema for AI chat."""
    company_id: int
    message: str = Field(..., min_length=1, max_length=4000)
    context_type: Literal["general", "payroll", "employee", "tax"] = "general"


class AiChatResponse(BaseSchema):
    """Response schema for AI chat."""
    role: str = "assistant"
    content: str
    tokens_used: Optional[int] = None


# --- Report Schemas ---

class AiReportRequest(BaseSchema):
    """Request schema for AI report generation."""
    company_id: int
    report_type: Literal["payroll_summary", "overtime_analysis", "tax_compliance", "employee_insights"]
    period_month: Optional[int] = Field(None, ge=1, le=12)
    period_year: Optional[int] = Field(None, ge=2020, le=2030)


class AiReportResponse(BaseSchema):
    """Response schema for AI-generated report."""
    report_title: str
    report_content: str
    generated_at: datetime
    model_used: str


# --- Test Connection ---

class AiTestConnectionRequest(BaseSchema):
    """Request schema for testing AI connection."""
    company_id: int


class AiTestConnectionResponse(BaseSchema):
    """Response schema for connection test."""
    status: Literal["ok", "error"]
    message: str
    latency_ms: Optional[int] = None
