"""
Pydantic schemas for Attendance and Overtime API contracts.
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Optional, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, PaginatedResponse


# --- Attendance Summary Schemas ---


class AttendanceSummaryResponse(BaseSchema):
    """Monthly attendance summary per employee."""

    employee_id: int
    employee_code: str
    employee_name: str
    total_working_days: int
    present_days: int
    absent_days: int
    sick_days: int
    leave_days: int
    permitted_days: int
    late_minutes: int
    attendance_percentage: float


# --- Attendance Schemas ---


class AttendanceRecordCreate(BaseSchema):
    """Request schema for creating an attendance record."""

    employee_id: int
    attendance_date: date
    shift_id: Optional[int] = None
    check_in_time: Optional[str] = Field(None, max_length=8, description="HH:MM:SS format")
    check_out_time: Optional[str] = Field(None, max_length=8, description="HH:MM:SS format")
    status: Literal["PRESENT", "ABSENT", "LEAVE", "SICK", "PERMITTED"]
    notes: Optional[str] = None

    @field_validator("check_in_time", "check_out_time")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re

        if not re.match(r"^\d{2}:\d{2}(:\d{2})?$", v):
            raise ValueError("Time must be in HH:MM or HH:MM:SS format")
        return v


class AttendanceRecordResponse(BaseSchema):
    """Response schema for an attendance record."""

    id: int
    employee_id: int
    attendance_date: date
    status: str
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    is_late: bool
    late_minutes: int
    hours_worked: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class AttendanceRecordListResponse(PaginatedResponse[AttendanceRecordResponse]):
    """Paginated list of attendance records."""

    pass


# --- Overtime Schemas ---


class OvertimeRecordCreate(BaseSchema):
    """Request schema for creating an overtime record."""

    employee_id: int
    overtime_date: date
    overtime_type: Literal["WEEKDAY", "WEEKEND", "HOLIDAY"]
    hours: Decimal = Field(..., gt=0, description="Overtime hours worked")
    notes: Optional[str] = None


class OvertimeRecordResponse(BaseSchema):
    """Response schema for an overtime record."""

    id: int
    employee_id: int
    overtime_date: date
    overtime_type: str
    hours: Decimal
    multiplier: Decimal
    calculated_amount: Optional[Decimal] = None
    approval_status: str
    approved_by: Optional[int] = None
    approval_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class OvertimeApprovalRequest(BaseSchema):
    """Request schema for approving/rejecting overtime."""

    approval_status: Literal["APPROVED", "REJECTED"]
    approved_by: int


class OvertimeRecordListResponse(PaginatedResponse[OvertimeRecordResponse]):
    """Paginated list of overtime records."""

    pass
