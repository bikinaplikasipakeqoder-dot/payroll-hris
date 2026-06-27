"""
Pydantic schemas for master/reference data CRUD operations.
"""

from typing import Optional

from pydantic import BaseModel


# ─── Department ───────────────────────────────────────────────────────────────

class DepartmentCreate(BaseModel):
    company_id: int = 1
    code: str
    name: str

class DepartmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

class DepartmentResponse(BaseModel):
    id: int
    company_id: int
    code: str
    name: str

    class Config:
        from_attributes = True


# ─── Position ─────────────────────────────────────────────────────────────────

class PositionCreate(BaseModel):
    company_id: int = 1
    code: str
    name: str

class PositionUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None

class PositionResponse(BaseModel):
    id: int
    company_id: int
    code: str
    name: str

    class Config:
        from_attributes = True


# ─── Grade ────────────────────────────────────────────────────────────────────

class GradeCreate(BaseModel):
    company_id: int = 1
    grade_code: str
    grade_name: str

class GradeUpdate(BaseModel):
    grade_code: Optional[str] = None
    grade_name: Optional[str] = None

class GradeResponse(BaseModel):
    id: int
    company_id: int
    grade_code: str
    grade_name: str

    class Config:
        from_attributes = True


# ─── Employment Status ────────────────────────────────────────────────────────

class EmploymentStatusCreate(BaseModel):
    company_id: int = 1
    name: str
    code: str

class EmploymentStatusUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None

class EmploymentStatusResponse(BaseModel):
    id: int
    company_id: int
    name: str
    code: str

    class Config:
        from_attributes = True


# ─── Working Days Configuration ───────────────────────────────────────────────

class WorkingDaysConfigCreate(BaseModel):
    company_id: int = 1
    year: int
    month: int
    working_days: int


class WorkingDaysConfigUpdate(BaseModel):
    working_days: int


class WorkingDaysConfigResponse(BaseModel):
    id: int
    company_id: int
    year: int
    month: int
    working_days: int

    class Config:
        from_attributes = True
