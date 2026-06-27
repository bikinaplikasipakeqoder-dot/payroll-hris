"""
Integration, localization, and audit models for the Payroll & HRIS system.

Tables:
- ai_settings: AI integration configuration per company
- languages: Supported languages for the system
- translations: Translation strings for i18n support
- audit_logs: System-wide audit trail
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin


class AiSetting(Base, TimestampMixin):
    """AI integration configuration per company."""

    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, unique=True)
    provider_name = Column(String(100), nullable=False)
    api_key = Column(Text, nullable=True)
    api_host = Column(String(500), nullable=True)
    model_name = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=True)
    temperature = Column(Numeric(3, 2), default=0.7)
    max_tokens = Column(Integer, default=2048)
    is_active = Column(Boolean, default=False)


class Language(Base, TimestampMixin):
    """Supported languages for the system."""

    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(String(10), unique=True, nullable=False)
    language_name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    translations = relationship("Translation", backref="language")


class Translation(Base, TimestampMixin):
    """Translation strings for internationalization support."""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    translation_key = Column(String(255), nullable=False)
    translation_value = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)

    __table_args__ = (
        UniqueConstraint("language_id", "translation_key", name="uq_translations_lang_key"),
        Index("idx_translations_key", "language_id", "translation_key"),
    )


class AuditLog(Base):
    """System-wide audit trail for tracking all significant actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    action = Column(String(50), nullable=False)
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "action IN ('CREATE', 'UPDATE', 'DELETE', 'APPROVE', 'EXPORT', 'LOGIN')",
            name="ck_audit_logs_action",
        ),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user_date", "user_id", "created_at"),
    )


class Notification(Base, TimestampMixin):
    """In-app notification system."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    link = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('PAYSLIP_READY', 'BULK_COMPLETE', 'BULK_FAILED')",
            name="ck_notifications_type",
        ),
        Index("idx_notifications_employee_read", "employee_id", "is_read"),
        Index("idx_notifications_user_read", "user_id", "is_read"),
    )
