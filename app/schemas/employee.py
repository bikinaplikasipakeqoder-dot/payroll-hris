"""
Pydantic schemas for Employee API contracts.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, PaginatedResponse


class EmployeeCreate(BaseSchema):
    """Request schema for creating a new employee."""

    company_id: int
    employee_code: str = Field(..., max_length=50)
    first_name: str = Field(..., max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    personal_id_number: Optional[str] = Field(None, max_length=50)
    npwp_number: Optional[str] = Field(None, max_length=50)
    ptkp_status: Literal[
        "TK/0", "TK/1", "TK/2", "TK/3", "K/0", "K/1", "K/2", "K/3"
    ] = "TK/0"
    religion: Literal[
        "Islam", "Protestan", "Katolik", "Hindu", "Buddha", "Konghucu"
    ] = "Islam"
    gender: Optional[Literal["M", "F"]] = None
    date_of_birth: Optional[date] = None
    date_joined: date
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    grade_id: Optional[int] = None
    employment_status_id: Optional[int] = None
    entity_id: Optional[int] = None
    base_salary: Optional[Decimal] = None
    base_salary_effective_date: Optional[date] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_account_name: Optional[str] = Field(None, max_length=255)
    bpjs_kes_number: Optional[str] = Field(None, max_length=30)
    bpjs_tk_number: Optional[str] = Field(None, max_length=30)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address_street: Optional[str] = None
    address_city: Optional[str] = Field(None, max_length=100)
    address_province: Optional[str] = Field(None, max_length=100)
    address_postal_code: Optional[str] = Field(None, max_length=10)


class EmployeeUpdate(BaseSchema):
    """Request schema for updating an employee (PATCH - all fields optional)."""

    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    personal_id_number: Optional[str] = Field(None, max_length=50)
    npwp_number: Optional[str] = Field(None, max_length=50)
    ptkp_status: Optional[
        Literal["TK/0", "TK/1", "TK/2", "TK/3", "K/0", "K/1", "K/2", "K/3"]
    ] = None
    religion: Optional[
        Literal["Islam", "Protestan", "Katolik", "Hindu", "Buddha", "Konghucu"]
    ] = None
    gender: Optional[Literal["M", "F"]] = None
    date_of_birth: Optional[date] = None
    date_joined: Optional[date] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    grade_id: Optional[int] = None
    employment_status_id: Optional[int] = None
    entity_id: Optional[int] = None
    base_salary: Optional[Decimal] = None
    base_salary_effective_date: Optional[date] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=50)
    bank_account_name: Optional[str] = Field(None, max_length=255)
    bpjs_kes_number: Optional[str] = Field(None, max_length=30)
    bpjs_tk_number: Optional[str] = Field(None, max_length=30)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    address_street: Optional[str] = None
    address_city: Optional[str] = Field(None, max_length=100)
    address_province: Optional[str] = Field(None, max_length=100)
    address_postal_code: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None


class EmployeeResponse(BaseSchema):
    """Response schema for an employee."""

    id: int
    company_id: int
    employee_code: str
    first_name: str
    last_name: Optional[str] = None
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    personal_id_number: Optional[str] = None
    npwp: Optional[str] = None
    ptkp_status: str
    religion: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_province: Optional[str] = None
    address_postal_code: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    grade_id: Optional[int] = None
    employment_status_id: Optional[int] = None
    entity_id: Optional[int] = None
    date_joined: date
    date_left: Optional[date] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_account_holder_name: Optional[str] = None
    base_salary: Optional[Decimal] = None
    base_salary_effective_date: Optional[date] = None
    bpjs_kesehatan_number: Optional[str] = None
    bpjs_ketenagakerjaan_number: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class EmployeeListResponse(PaginatedResponse[EmployeeResponse]):
    """Paginated list of employees."""

    pass
