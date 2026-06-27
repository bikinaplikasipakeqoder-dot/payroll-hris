"""
Kasbon (employee loan/advance) models for the Payroll & HRIS system.

Tables:
- kasbon_requests: Employee loan/advance requests
- kasbon_installments: Installment schedule and payment tracking
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class KasbonRequest(Base, TimestampMixin):
    """Employee loan/advance (kasbon) requests."""

    __tablename__ = "kasbon_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    kasbon_number = Column(String(50), unique=True, nullable=False)
    principal_amount = Column(Numeric(15, 2), nullable=False)
    purpose = Column(Text, nullable=False)
    request_date = Column(Date, nullable=False)
    approval_date = Column(Date, nullable=True)
    disbursement_date = Column(Date, nullable=True)
    number_of_installments = Column(Integer, nullable=False)
    installment_amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    installments = relationship("KasbonInstallment", backref="kasbon_request")

    __table_args__ = (
        CheckConstraint(
            "principal_amount > 0",
            name="ck_kasbon_requests_principal_positive",
        ),
        CheckConstraint(
            "number_of_installments > 0",
            name="ck_kasbon_requests_installments_positive",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'DISBURSED', 'COMPLETED', 'REJECTED')",
            name="ck_kasbon_requests_status",
        ),
        Index("idx_kasbon_employee", "employee_id"),
        Index("idx_kasbon_status", "status"),
    )


class KasbonInstallment(Base, TimestampMixin):
    """Installment schedule and payment tracking for kasbon."""

    __tablename__ = "kasbon_installments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kasbon_request_id = Column(Integer, ForeignKey("kasbon_requests.id"), nullable=False)
    installment_number = Column(Integer, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)
    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "kasbon_request_id", "installment_number",
            name="uq_kasbon_installments_request_number",
        ),
    )
