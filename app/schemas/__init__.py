"""
Pydantic schemas for the Payroll & HRIS system API contracts.
"""

from app.schemas.base import (
    BaseSchema,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
)

from app.schemas.payroll import (
    PayrollRunCreate,
    PayrollRunResponse,
    PayrollRunListResponse,
    PayslipResponse,
    PayslipLineResponse,
    PayslipDetailResponse,
)

from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeListResponse,
)

from app.schemas.tax import (
    TaxSettingResponse,
    TaxSettingUpdate,
    PtkpValueResponse,
    TaxBracketResponse,
    TerBracketResponse,
)

from app.schemas.bpjs import (
    BpjsSettingResponse,
    BpjsSettingUpdate,
)

from app.schemas.attendance import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceRecordListResponse,
    OvertimeRecordCreate,
    OvertimeRecordResponse,
    OvertimeApprovalRequest,
    OvertimeRecordListResponse,
)

__all__ = [
    # Base
    "BaseSchema",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    # Payroll
    "PayrollRunCreate",
    "PayrollRunResponse",
    "PayrollRunListResponse",
    "PayslipResponse",
    "PayslipLineResponse",
    "PayslipDetailResponse",
    # Employee
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "EmployeeListResponse",
    # Tax
    "TaxSettingResponse",
    "TaxSettingUpdate",
    "PtkpValueResponse",
    "TaxBracketResponse",
    "TerBracketResponse",
    # BPJS
    "BpjsSettingResponse",
    "BpjsSettingUpdate",
    # Attendance
    "AttendanceRecordCreate",
    "AttendanceRecordResponse",
    "AttendanceRecordListResponse",
    "OvertimeRecordCreate",
    "OvertimeRecordResponse",
    "OvertimeApprovalRequest",
    "OvertimeRecordListResponse",
]
