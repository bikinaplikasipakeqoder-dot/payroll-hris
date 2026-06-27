"""
FastAPI routers for the Payroll & HRIS system.
"""

from app.routers.payroll import router as payroll_router
from app.routers.employees import router as employees_router
from app.routers.tax import router as tax_router
from app.routers.bpjs import router as bpjs_router
from app.routers.attendance import router as attendance_router
from app.routers.ai import router as ai_router
from app.routers.excel import router as excel_router
from app.routers.payslip import router as payslip_router
from app.routers.notification import router as notification_router
from app.routers.master_data import router as master_data_router
from app.routers.allowances import router as allowances_router
from app.routers.deductions import router as deductions_router
from app.routers.bonuses import router as bonuses_router
from app.routers.reimbursements import router as reimbursements_router
from app.routers.kasbon import router as kasbon_router
from app.routers.thr import router as thr_router
from app.routers.company_entities import router as company_entities_router
from app.routers.rules import router as rules_router

__all__ = [
    "payroll_router",
    "employees_router",
    "tax_router",
    "bpjs_router",
    "attendance_router",
    "ai_router",
    "excel_router",
    "payslip_router",
    "notification_router",
    "master_data_router",
    "allowances_router",
    "deductions_router",
    "bonuses_router",
    "reimbursements_router",
    "kasbon_router",
    "thr_router",
    "company_entities_router",
    "rules_router",
]
