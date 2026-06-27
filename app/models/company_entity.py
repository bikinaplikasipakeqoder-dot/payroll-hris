"""
Company entities and regional minimum wage (UMP) settings.

Supports multi-location payroll where one company can have many entities
(branches/locations), each subject to a province/city-specific UMP.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Date, Text,
    ForeignKey, Index, UniqueConstraint, Numeric,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Entity(Base, TimestampMixin):
    """A company branch/location where employees are assigned."""

    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    country = Column(String(100), default="Indonesia", nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationship
    company = relationship("Company", backref="entities")

    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_entities_company_code"),
        Index("idx_entities_company_active", "company_id", "is_active"),
    )


class UmpSetting(Base, TimestampMixin):
    """Regional minimum wage (UMP/UMK) master data per province/city."""

    __tablename__ = "ump_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    province = Column(String(100), nullable=False)
    city = Column(String(100), nullable=True)
    amount = Column(Numeric(15, 2), nullable=False)
    effective_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationship
    company = relationship("Company", backref="ump_settings")

    __table_args__ = (
        UniqueConstraint(
            "company_id", "province", "city", "effective_date",
            name="uq_ump_settings_company_location_effective",
        ),
        Index("idx_ump_settings_company", "company_id"),
        Index("idx_ump_settings_location", "province", "city"),
    )
