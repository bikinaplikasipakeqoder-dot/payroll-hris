"""Excel Import/Export API endpoints."""
import io
from fastapi import APIRouter, Depends, File, Query, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.schemas.excel import ImportResult, ImportRowError
from app.services.excel_import_service import ExcelImportService
from app.services.excel_export_service import ExcelExportService

router = APIRouter(prefix="/excel", tags=["Excel Import/Export"])


# --- Import Endpoints ---

@router.post("/import/employees", response_model=ImportResult)
def import_employees(
    file: UploadFile = File(...),
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Bulk import employees from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "File must be .xlsx or .xls")

    contents = file.file.read()
    result, error_bytes = ExcelImportService.import_employees(contents, company_id, db)

    # If there are errors, return the error file as Excel download
    if error_bytes:
        return StreamingResponse(
            io.BytesIO(error_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=import_errors.xlsx"}
        )

    return ImportResult(**result)


@router.post("/import/attendance", response_model=ImportResult)
def import_attendance(
    file: UploadFile = File(...),
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Bulk import attendance records from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "File must be .xlsx or .xls")

    contents = file.file.read()
    result, error_bytes = ExcelImportService.import_attendance(contents, company_id, db)

    if error_bytes:
        return StreamingResponse(
            io.BytesIO(error_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=attendance_errors.xlsx"}
        )

    return ImportResult(**result)


@router.post("/import/allowances", response_model=ImportResult)
def import_allowances(
    file: UploadFile = File(...),
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Bulk import employee allowances from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "File must be .xlsx or .xls")

    contents = file.file.read()
    result, error_bytes = ExcelImportService.import_allowances(contents, company_id, db)

    if error_bytes:
        return StreamingResponse(
            io.BytesIO(error_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=allowance_errors.xlsx"}
        )

    return ImportResult(**result)


@router.post("/import/bonuses", response_model=ImportResult)
def import_bonuses(
    file: UploadFile = File(...),
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Bulk import bonus records from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "File must be .xlsx or .xls")

    contents = file.file.read()
    result, error_bytes = ExcelImportService.import_bonuses(contents, company_id, db)

    if error_bytes:
        return StreamingResponse(
            io.BytesIO(error_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=bonus_errors.xlsx"}
        )

    return ImportResult(**result)


@router.post("/import/thr", response_model=ImportResult)
def import_thr(
    file: UploadFile = File(...),
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Bulk import THR records from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "File must be .xlsx or .xls")

    contents = file.file.read()
    result, error_bytes = ExcelImportService.import_thr(contents, company_id, db)

    if error_bytes:
        return StreamingResponse(
            io.BytesIO(error_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=thr_errors.xlsx"}
        )

    return ImportResult(**result)


@router.post("/import/reimbursements", response_model=ImportResult)
def import_reimbursements(
    file: UploadFile = File(...),
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Bulk import reimbursement claims from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "File must be .xlsx or .xls")

    contents = file.file.read()
    result, error_bytes = ExcelImportService.import_reimbursements(contents, company_id, db)

    if error_bytes:
        return StreamingResponse(
            io.BytesIO(error_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=reimbursement_errors.xlsx"}
        )

    return ImportResult(**result)


@router.post("/import/kasbon", response_model=ImportResult)
def import_kasbon(
    file: UploadFile = File(...),
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Bulk import kasbon/loan records from Excel file."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "File must be .xlsx or .xls")

    contents = file.file.read()
    result, error_bytes = ExcelImportService.import_kasbon(contents, company_id, db)

    if error_bytes:
        return StreamingResponse(
            io.BytesIO(error_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=kasbon_errors.xlsx"}
        )

    return ImportResult(**result)


# --- Export Endpoints ---

@router.get("/export/payslips/{payroll_run_id}")
def export_payslips(payroll_run_id: int, db: Session = Depends(get_db)):
    """Export payslips for a payroll run as Excel."""
    data = ExcelExportService.export_payslips(payroll_run_id, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=payslips_run_{payroll_run_id}.xlsx"}
    )


@router.get("/export/payroll-summary/{payroll_run_id}")
def export_payroll_summary(payroll_run_id: int, db: Session = Depends(get_db)):
    """Export payroll summary by department as Excel."""
    data = ExcelExportService.export_payroll_summary(payroll_run_id, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=payroll_summary_{payroll_run_id}.xlsx"}
    )


@router.get("/export/bpjs-recap")
def export_bpjs_recap(
    company_id: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2030),
    db: Session = Depends(get_db),
):
    """Export BPJS recap for a month as Excel."""
    data = ExcelExportService.export_bpjs_recap(company_id, month, year, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=bpjs_recap_{year}_{month:02d}.xlsx"}
    )


@router.get("/export/tax-recap")
def export_tax_recap(
    company_id: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2030),
    db: Session = Depends(get_db),
):
    """Export tax (PPh 21) recap for a month as Excel."""
    data = ExcelExportService.export_tax_recap(company_id, month, year, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=tax_recap_{year}_{month:02d}.xlsx"}
    )


@router.get("/export/attendance")
def export_attendance(
    company_id: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2030),
    db: Session = Depends(get_db),
):
    """Export attendance records for a month as Excel."""
    data = ExcelExportService.export_attendance(company_id, month, year, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=attendance_{year}_{month:02d}.xlsx"}
    )


@router.get("/export/bonuses")
def export_bonuses(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Export bonus records for a company as Excel."""
    data = ExcelExportService.export_bonuses(company_id, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=bonuses_{company_id}.xlsx"}
    )


@router.get("/export/thr")
def export_thr(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Export THR records for a company as Excel."""
    data = ExcelExportService.export_thr(company_id, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=thr_{company_id}.xlsx"}
    )


@router.get("/export/reimbursements")
def export_reimbursements(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Export reimbursement claims for a company as Excel."""
    data = ExcelExportService.export_reimbursements(company_id, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=reimbursements_{company_id}.xlsx"}
    )


@router.get("/export/kasbon")
def export_kasbon(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Export kasbon/loan records for a company as Excel."""
    data = ExcelExportService.export_kasbon(company_id, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=kasbon_{company_id}.xlsx"}
    )


# --- Template Endpoints ---

@router.get("/templates/attendance")
def download_attendance_template():
    """Download an empty attendance import template."""
    data = ExcelExportService.generate_attendance_template()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=attendance_template.xlsx"}
    )


@router.get("/templates/bonuses")
def download_bonus_template(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Download an empty bonus import template."""
    data = ExcelExportService.generate_bonus_template(company_id, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=bonus_template.xlsx"}
    )


@router.get("/templates/thr")
def download_thr_template():
    """Download an empty THR import template."""
    data = ExcelExportService.generate_thr_template()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=thr_template.xlsx"}
    )


@router.get("/templates/reimbursements")
def download_reimbursement_template(
    company_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Download an empty reimbursement import template."""
    data = ExcelExportService.generate_reimbursement_template(company_id, db)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reimbursement_template.xlsx"}
    )


@router.get("/templates/kasbon")
def download_kasbon_template():
    """Download an empty kasbon import template."""
    data = ExcelExportService.generate_kasbon_template()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=kasbon_template.xlsx"}
    )


# --- Admin Seed Endpoint ---

@router.post("/admin/seed-bulk", tags=["Admin"])
def trigger_bulk_seed(company_id: int = 1, count: int = 200, db: Session = Depends(get_db)):
    """Trigger bulk employee seeding via API (admin only)."""
    from app.seed.bulk_seeder import seed_bulk_employees
    seed_bulk_employees(db, company_id=company_id, count=count)
    db.commit()
    return {"message": f"Seeding completed for company {company_id}"}
