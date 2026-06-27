"""E-Payslip PDF generation and management endpoints."""

from pathlib import Path
from io import BytesIO

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.payroll import (
    Payslip, PayrollRun, PayslipTemplate, PayslipRecord, PayslipGenerationJob
)
from app.models.employee import Employee
from app.schemas.payslip_pdf import (
    BulkGenerateRequest, JobStatusResponse, PayslipRecordResponse,
    PayslipTemplateRequest, PayslipTemplateResponse,
    AnnualSummaryMonth, AnnualSummaryResponse,
)
from app.services.payslip_pdf_service import PayslipPdfService
from app.services.payslip_bulk_service import PayslipBulkService

router = APIRouter(prefix="/payslip", tags=["E-Payslip"])

MONTH_NAMES_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


# --- Single Payslip PDF ---

@router.get("/{employee_id}/{year}/{month}")
def get_payslip_pdf(
    employee_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """Get or generate payslip PDF for employee/period."""
    # Check if a completed record exists on disk
    existing_record = (
        db.query(PayslipRecord)
        .filter(
            PayslipRecord.employee_id == employee_id,
            PayslipRecord.year == year,
            PayslipRecord.month == month,
            PayslipRecord.status == "COMPLETED",
        )
        .first()
    )

    if existing_record and existing_record.file_path:
        file_path = Path(existing_record.file_path)
        if file_path.exists():
            pdf_bytes = file_path.read_bytes()
            filename = file_path.name
            return StreamingResponse(
                BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )

    # Generate a new PDF
    try:
        pdf_bytes, filename = PayslipPdfService.generate_single_payslip(
            employee_id, year, month, db
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Bulk Generation ---

@router.post("/bulk-generate")
def bulk_generate(
    request: BulkGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Start bulk payslip PDF generation as a background job."""
    try:
        job_id = PayslipBulkService.start_bulk_generation(
            request.payroll_run_id, request.company_id, db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(PayslipBulkService.process_bulk_job, job_id)
    return {"job_id": job_id, "status": "QUEUED"}


# --- Job Status ---

@router.get("/job-status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get the status of a bulk payslip generation job."""
    job = PayslipBulkService.get_job_status(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress_percent = 0.0
    if job.total_count > 0:
        progress_percent = (job.completed_count / job.total_count) * 100

    result_file_url = None
    if job.status == "COMPLETED":
        result_file_url = f"/api/v1/payslip/job/{job_id}/download"

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        total_count=job.total_count,
        completed_count=job.completed_count,
        failed_count=job.failed_count,
        progress_percent=round(progress_percent, 1),
        result_file_url=result_file_url,
        error_message=job.error_message,
    )


# --- Job Download ---

@router.get("/job/{job_id}/download")
def download_job_zip(job_id: str, db: Session = Depends(get_db)):
    """Download the ZIP file from a completed bulk generation job."""
    job = PayslipBulkService.get_job_status(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job.status}",
        )

    if not job.result_file_path:
        raise HTTPException(status_code=404, detail="Result file not available")

    zip_path = Path(job.result_file_path)
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="ZIP file not found on disk")

    zip_bytes = zip_path.read_bytes()
    return StreamingResponse(
        BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="payslips_{job_id}.zip"'
        },
    )


# --- Payslip History ---

@router.get("/history", response_model=list[PayslipRecordResponse])
def get_payslip_history(
    employee_id: int = Query(...),
    year: int = Query(None),
    month: int = Query(None),
    db: Session = Depends(get_db),
):
    """Get payslip generation history for an employee."""
    query = (
        db.query(PayslipRecord, Employee, Payslip)
        .join(Employee, PayslipRecord.employee_id == Employee.id)
        .outerjoin(Payslip, PayslipRecord.payslip_id == Payslip.id)
        .filter(PayslipRecord.employee_id == employee_id)
    )

    if year is not None:
        query = query.filter(PayslipRecord.year == year)
    if month is not None:
        query = query.filter(PayslipRecord.month == month)

    query = query.order_by(PayslipRecord.year.desc(), PayslipRecord.month.desc())
    results = query.all()

    response = []
    for record, employee, payslip in results:
        response.append(
            PayslipRecordResponse(
                id=record.id,
                year=record.year,
                month=record.month,
                employee_code=employee.employee_code or "",
                employee_name=employee.full_name or "",
                gross_salary=float(payslip.gross_salary) if payslip and payslip.gross_salary else 0.0,
                net_salary=float(payslip.net_salary) if payslip and payslip.net_salary else 0.0,
                status=record.status,
                generated_at=record.generated_at.isoformat() if record.generated_at else None,
            )
        )

    return response


# --- Annual Summary ---

@router.get("/annual-summary/{employee_id}/{year}", response_model=AnnualSummaryResponse)
def get_annual_summary(employee_id: int, year: int, db: Session = Depends(get_db)):
    """Get annual payslip summary for an employee."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Find all PayrollRuns for the given year
    payroll_runs = (
        db.query(PayrollRun)
        .filter(PayrollRun.payroll_period.like(f"{year}-%"))
        .all()
    )

    if not payroll_runs:
        raise HTTPException(status_code=404, detail=f"No payroll data found for year {year}")

    run_ids = [run.id for run in payroll_runs]

    # Find all payslips for this employee in those runs
    payslips = (
        db.query(Payslip)
        .filter(
            Payslip.employee_id == employee_id,
            Payslip.payroll_run_id.in_(run_ids),
        )
        .all()
    )

    if not payslips:
        raise HTTPException(
            status_code=404,
            detail=f"No payslips found for employee {employee_id} in year {year}",
        )

    # Map payroll_run_id -> payroll_period for month extraction
    run_period_map = {run.id: run.payroll_period for run in payroll_runs}

    months_data = []
    ytd_gross = 0.0
    ytd_deductions = 0.0
    ytd_tax = 0.0
    ytd_bpjs = 0.0
    ytd_net = 0.0

    for ps in payslips:
        period = run_period_map.get(ps.payroll_run_id, "")
        try:
            month_num = int(period.split("-")[1])
        except (IndexError, ValueError):
            continue

        gross = float(ps.gross_salary or 0)
        deductions = float(ps.total_deductions or 0)
        tax = float(ps.pph21_tax or 0)
        bpjs = float(ps.bpjs_kes_employee or 0) + float(ps.bpjs_jht_employee or 0) + float(ps.bpjs_jp_employee or 0)
        net = float(ps.net_salary or 0)

        months_data.append(
            AnnualSummaryMonth(
                month=month_num,
                month_name=MONTH_NAMES_ID[month_num],
                gross_salary=gross,
                total_deductions=deductions,
                pph21_tax=tax,
                bpjs_total=bpjs,
                net_salary=net,
            )
        )

        ytd_gross += gross
        ytd_deductions += deductions
        ytd_tax += tax
        ytd_bpjs += bpjs
        ytd_net += net

    # Sort by month
    months_data.sort(key=lambda m: m.month)

    return AnnualSummaryResponse(
        employee_id=employee_id,
        employee_name=employee.full_name or "",
        year=year,
        months=months_data,
        ytd_gross=round(ytd_gross, 2),
        ytd_deductions=round(ytd_deductions, 2),
        ytd_tax=round(ytd_tax, 2),
        ytd_bpjs=round(ytd_bpjs, 2),
        ytd_net=round(ytd_net, 2),
    )


# --- Templates CRUD ---

@router.get("/templates", response_model=list[PayslipTemplateResponse])
def list_templates(
    company_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """List all active payslip templates for a company."""
    templates = (
        db.query(PayslipTemplate)
        .filter(
            PayslipTemplate.company_id == company_id,
            PayslipTemplate.is_active == True,
        )
        .all()
    )

    return [
        PayslipTemplateResponse(
            id=t.id,
            template_name=t.template_name,
            html_content=t.html_content,
            css_content=t.css_content,
            is_default=t.is_default,
            is_active=t.is_active,
        )
        for t in templates
    ]


@router.post("/templates", response_model=PayslipTemplateResponse, status_code=201)
def create_template(
    request: PayslipTemplateRequest,
    company_id: int = Query(1),
    db: Session = Depends(get_db),
):
    """Create a new payslip template."""
    template = PayslipTemplate(
        company_id=company_id,
        template_name=request.template_name,
        html_content=request.html_content,
        css_content=request.css_content,
        is_default=request.is_default,
        is_active=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return PayslipTemplateResponse(
        id=template.id,
        template_name=template.template_name,
        html_content=template.html_content,
        css_content=template.css_content,
        is_default=template.is_default,
        is_active=template.is_active,
    )


@router.put("/templates/{template_id}", response_model=PayslipTemplateResponse)
def update_template(
    template_id: int,
    request: PayslipTemplateRequest,
    db: Session = Depends(get_db),
):
    """Update an existing payslip template."""
    template = db.query(PayslipTemplate).filter(PayslipTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    template.template_name = request.template_name
    template.html_content = request.html_content
    template.css_content = request.css_content
    template.is_default = request.is_default

    db.commit()
    db.refresh(template)

    return PayslipTemplateResponse(
        id=template.id,
        template_name=template.template_name,
        html_content=template.html_content,
        css_content=template.css_content,
        is_default=template.is_default,
        is_active=template.is_active,
    )


# --- Template Preview ---

@router.post("/templates/preview")
def preview_template(
    request: PayslipTemplateRequest,
    db: Session = Depends(get_db),
):
    """Preview a payslip template with sample data, returns PDF."""
    # Find a sample payslip from DB
    sample_payslip = db.query(Payslip).first()
    if not sample_payslip:
        raise HTTPException(
            status_code=404,
            detail="No sample payslip data available for preview",
        )

    # Load related data
    employee = db.query(Employee).filter(Employee.id == sample_payslip.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Sample employee not found")

    from app.models.employee import Department, Position
    from app.models.auth import Company

    department_name = ""
    if employee.department_id:
        dept = db.query(Department).filter(Department.id == employee.department_id).first()
        department_name = dept.name if dept else ""

    position_name = ""
    if employee.position_id:
        pos = db.query(Position).filter(Position.id == employee.position_id).first()
        position_name = pos.name if pos else ""

    company = db.query(Company).filter(Company.id == employee.company_id).first()
    if not company:
        company = Company(name="Preview Company", address="", phone="", email="")

    # Attach payroll_run for period label
    payroll_run = (
        db.query(PayrollRun)
        .filter(PayrollRun.id == sample_payslip.payroll_run_id)
        .first()
    )
    if payroll_run:
        sample_payslip.payroll_run = payroll_run

    # Render with the provided template
    html = PayslipPdfService.render_html(
        payslip=sample_payslip,
        employee=employee,
        company=company,
        department_name=department_name,
        position_name=position_name,
        template_html=request.html_content,
        css=request.css_content,
    )
    pdf_bytes = PayslipPdfService.generate_pdf(html)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="template_preview.pdf"'},
    )
