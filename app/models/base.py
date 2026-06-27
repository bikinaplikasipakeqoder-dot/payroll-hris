"""
Base model classes and mixins for the Payroll & HRIS system.

Provides:
- Base: SQLAlchemy declarative base class
- TimestampMixin: Automatic created_at/updated_at timestamps
- SoftDeleteMixin: Soft delete capability with is_deleted flag
- AuditMixin: Tracks who created/updated records
"""

from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, Boolean, String
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """SQLAlchemy declarative base class for all models."""
    pass


class TimestampMixin:
    """Provides created_at and updated_at timestamps."""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Provides soft delete capability."""

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime, nullable=True)


class AuditMixin:
    """Tracks who created/updated records."""

    @declared_attr
    def created_by(cls):
        return Column(Integer, nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(Integer, nullable=True)
