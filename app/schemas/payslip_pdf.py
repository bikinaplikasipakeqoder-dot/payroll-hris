"""Pydantic schemas for E-Payslip PDF generation."""

from typing import Optional

from pydantic import BaseModel


class BulkGenerateRequest(BaseModel):
    payroll_run_id: int
    company_id: int = 1


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    total_count: int
    completed_count: int
    failed_count: int
    progress_percent: float
    result_file_url: Optional[str] = None
    error_message: Optional[str] = None


class PayslipRecordResponse(BaseModel):
    id: int
    year: int
    month: int
    employee_code: str
    employee_name: str
    gross_salary: float
    net_salary: float
    status: str
    generated_at: Optional[str] = None


class PayslipTemplateRequest(BaseModel):
    template_name: str
    html_content: str
    css_content: Optional[str] = None
    is_default: bool = False


class PayslipTemplateResponse(BaseModel):
    id: int
    template_name: str
    html_content: str
    css_content: Optional[str] = None
    is_default: bool
    is_active: bool


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    is_read: bool
    created_at: str


class AnnualSummaryMonth(BaseModel):
    month: int
    month_name: str
    gross_salary: float
    total_deductions: float
    pph21_tax: float
    bpjs_total: float
    net_salary: float


class AnnualSummaryResponse(BaseModel):
    employee_id: int
    employee_name: str
    year: int
    months: list[AnnualSummaryMonth]
    ytd_gross: float
    ytd_deductions: float
    ytd_tax: float
    ytd_bpjs: float
    ytd_net: float
