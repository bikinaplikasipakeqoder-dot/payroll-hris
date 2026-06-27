"""
Base Pydantic schemas for the Payroll & HRIS system.

Provides shared base classes, generic paginated response, and standard
error/success response models.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Generic, TypeVar
from datetime import datetime, date

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[dict] = None


class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None
