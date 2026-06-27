"""
Field visit tracking models for the Payroll & HRIS system.

Tables:
- field_visits: Employee field visit records
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)

from app.models.base import Base, TimestampMixin


class FieldVisit(Base, TimestampMixin):
    """Employee field visit records for tracking client visits and off-site work."""

    __tablename__ = "field_visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    visit_date = Column(Date, nullable=False)
    location = Column(String(255), nullable=True)
    purpose = Column(Text, nullable=True)
    client_name = Column(String(150), nullable=True)
    check_in_time = Column(String(8), nullable=True)
    check_out_time = Column(String(8), nullable=True)
    duration_hours = Column(Numeric(5, 2), nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_visits_employee_date", "employee_id", "visit_date"),
    )
