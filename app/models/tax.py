"""
Indonesian tax calculation models for the Payroll & HRIS system.

Tables:
- tax_settings: Company-level tax calculation configuration
- ptkp_values: PTKP (Penghasilan Tidak Kena Pajak) threshold values
- tax_brackets_pasal_17: Progressive tax brackets per PPh Pasal 17
- ter_brackets: TER (Tarif Efektif Rata-rata) brackets
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)

from app.models.base import Base, TimestampMixin


class TaxSetting(Base, TimestampMixin):
    """Company-level tax calculation configuration."""

    __tablename__ = "tax_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), unique=True, nullable=False)
    tax_calculation_method = Column(String(20), nullable=False, default="PASAL_17")
    payroll_method = Column(String(20), nullable=False, default="GROSS")
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "tax_calculation_method IN ('PASAL_17', 'TER')",
            name="ck_tax_settings_calculation_method",
        ),
        CheckConstraint(
            "payroll_method IN ('GROSS', 'GROSS_UP', 'NETT')",
            name="ck_tax_settings_payroll_method",
        ),
    )


class PtkpValue(Base, TimestampMixin):
    """PTKP (Penghasilan Tidak Kena Pajak) threshold values."""

    __tablename__ = "ptkp_values"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    ptkp_code = Column(String(10), nullable=False)
    description = Column(String(255), nullable=False)
    annual_amount = Column(Numeric(15, 2), nullable=False)
    monthly_amount = Column(Numeric(15, 2), nullable=False)
    regulation_year = Column(Integer, nullable=False)
    regulation_reference = Column(String(100), nullable=True)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "company_id", "ptkp_code", "effective_date",
            name="uq_ptkp_values_company_code_date",
        ),
        Index("idx_ptkp_active", "company_id", "is_active", "effective_date"),
    )


class TaxBracketPasal17(Base, TimestampMixin):
    """Progressive tax brackets per PPh Pasal 17."""

    __tablename__ = "tax_brackets_pasal_17"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    bracket_order = Column(Integer, nullable=False)
    income_range_min = Column(Numeric(15, 2), nullable=False)
    income_range_max = Column(Numeric(15, 2), nullable=True, comment="NULL means unbounded")
    tax_rate = Column(Numeric(5, 4), nullable=False)
    regulation_year = Column(Integer, nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "company_id", "bracket_order", "effective_date",
            name="uq_tax_brackets_pasal17_company_order_date",
        ),
        Index("idx_tax_brackets_active", "company_id", "is_active", "effective_date"),
    )


class TerBracket(Base, TimestampMixin):
    """TER (Tarif Efektif Rata-rata) brackets for simplified tax calculation."""

    __tablename__ = "ter_brackets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    category = Column(String(1), nullable=False)
    income_range_min = Column(Numeric(15, 2), nullable=False)
    income_range_max = Column(Numeric(15, 2), nullable=True)
    ter_rate = Column(Numeric(5, 4), nullable=False)
    regulation_year = Column(Integer, nullable=False)
    effective_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "category IN ('A', 'B', 'C')",
            name="ck_ter_brackets_category",
        ),
        UniqueConstraint(
            "company_id", "category", "income_range_min", "effective_date",
            name="uq_ter_brackets_company_cat_min_date",
        ),
        Index("idx_ter_category_active", "company_id", "category", "is_active"),
    )
