"""
Authentication and authorization models for the Payroll & HRIS system.

Tables:
- companies: Organization/company master data
- roles: User roles for RBAC
- permissions: Granular permissions by resource and action
- user_roles: Many-to-many relationship between users and roles
- role_permissions: Many-to-many relationship between roles and permissions
- users: System user accounts
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    """Organization/company master data."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    tax_number = Column(String(50), nullable=True, comment="NPWP")
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    postal_code = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    work_week_days = Column(Integer, default=5)
    payroll_method = Column(String(20), default="GROSS", nullable=False)
    default_language = Column(String(10), default="id")
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint(
            "payroll_method IN ('GROSS', 'GROSS_UP', 'NETT')",
            name="ck_companies_payroll_method",
        ),
    )


class Role(Base, TimestampMixin):
    """User roles for role-based access control."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False)

    # Relationships
    permissions = relationship(
        "Permission", secondary="role_permissions", back_populates="roles"
    )


class Permission(Base, TimestampMixin):
    """Granular permissions by resource and action."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)

    # Relationships
    roles = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )


class UserRole(Base):
    """Many-to-many relationship between users and roles."""

    __tablename__ = "user_roles"

    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )


class RolePermission(Base):
    """Many-to-many relationship between roles and permissions."""

    __tablename__ = "role_permissions"

    role_id = Column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id = Column(
        Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class User(Base, TimestampMixin):
    """System user accounts."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    roles = relationship("Role", secondary="user_roles", backref="users")

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_employee_id", "employee_id"),
    )
