"""
BPJS (Badan Penyelenggara Jaminan Sosial) configuration models.

Tables:
- bpjs_settings: BPJS contribution rates and salary caps per type
  (Kesehatan, JHT, JP, JKK, JKM)
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)

from app.models.base import Base, TimestampMixin


class BpjsSetting(Base, TimestampMixin):
    """BPJS contribution rates and salary caps per type."""

    __tablename__ = "bpjs_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    bpjs_type = Column(String(20), nullable=False)
    employee_rate = Column(Numeric(5, 4), nullable=False)
    employer_rate = Column(Numeric(5, 4), nullable=False)
    max_salary_base = Column(Numeric(15, 2), nullable=True)
    regulation_year = Column(Integer, nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "bpjs_type IN ('KESEHATAN', 'JHT', 'JP', 'JKK', 'JKM')",
            name="ck_bpjs_settings_bpjs_type",
        ),
        UniqueConstraint(
            "company_id", "bpjs_type", "effective_date",
            name="uq_bpjs_settings_company_type_date",
        ),
        Index("idx_bpjs_active", "company_id", "bpjs_type", "is_active"),
    )
