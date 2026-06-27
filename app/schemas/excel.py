"""Pydantic schemas for Excel import/export endpoints."""

from typing import Optional
from pydantic import Field
from app.schemas.base import BaseSchema


class ImportRowError(BaseSchema):
    """Single row error detail."""
    row: int
    field: Optional[str] = None
    message: str


class ImportResult(BaseSchema):
    """Response schema for import operations."""
    total_rows: int
    success_count: int
    error_count: int
    errors: list[ImportRowError] = Field(default_factory=list)
