"""Indonesian Payroll & HRIS System - Database Models Package"""

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin

# Auth & Company
from app.models.auth import Company, Role, Permission, UserRole, RolePermission, User

# Company Entities & UMP
from app.models.company_entity import Entity, UmpSetting

# Employee & Organization
from app.models.employee import Department, Position, EmploymentStatus, Employee

# Salary & Compensation
from app.models.salary import Grade, GradeSalaryMatrix, AllowanceType, EmployeeAllowance, DeductionType

# Tax
from app.models.tax import TaxSetting, PtkpValue, TaxBracketPasal17, TerBracket

# BPJS
from app.models.bpjs import BpjsSetting

# Attendance & Overtime
from app.models.attendance import Shift, EmployeeShiftAssignment, AttendanceRecord, OvertimeRecord, OvertimeSetting

# Leave
from app.models.leave import LeaveType, EmployeeLeaveBalance, LeaveRequest

# Kasbon
from app.models.kasbon import KasbonRequest, KasbonInstallment

# Bonus & Reimbursement
from app.models.bonus import BonusType, Bonus, THRRecord, ReimbursementType, Reimbursement

# Payroll
from app.models.payroll import PayrollRun, Payslip, PayslipLine, PayslipTemplate, PayslipRecord, PayslipGenerationJob

# Field Visit
from app.models.visit import FieldVisit

# Integration & Localization
from app.models.integration import AiSetting, Language, Translation, AuditLog, Notification

__all__ = [
    # Base
    "Base", "TimestampMixin", "SoftDeleteMixin", "AuditMixin",
    # Auth & Company
    "Company", "Role", "Permission", "UserRole", "RolePermission", "User",
    # Company Entities & UMP
    "Entity", "UmpSetting",
    # Employee & Organization
    "Department", "Position", "EmploymentStatus", "Employee",
    # Salary & Compensation
    "Grade", "GradeSalaryMatrix", "AllowanceType", "EmployeeAllowance", "DeductionType",
    # Tax
    "TaxSetting", "PtkpValue", "TaxBracketPasal17", "TerBracket",
    # BPJS
    "BpjsSetting",
    # Attendance & Overtime
    "Shift", "EmployeeShiftAssignment", "AttendanceRecord", "OvertimeRecord", "OvertimeSetting",
    # Leave
    "LeaveType", "EmployeeLeaveBalance", "LeaveRequest",
    # Kasbon
    "KasbonRequest", "KasbonInstallment",
    # Bonus & Reimbursement
    "BonusType", "Bonus", "THRRecord", "ReimbursementType", "Reimbursement",
    # Payroll
    "PayrollRun", "Payslip", "PayslipLine",
    "PayslipTemplate", "PayslipRecord", "PayslipGenerationJob",
    # Field Visit
    "FieldVisit",
    # Integration & Localization
    "AiSetting", "Language", "Translation", "AuditLog", "Notification",
]
