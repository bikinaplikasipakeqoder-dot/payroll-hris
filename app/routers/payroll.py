"""
Payroll API endpoints — create, process, approve, and retrieve payroll runs.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from datetime import date

from app.database import get_db
from app.exceptions import (
    DuplicatePayrollRunError,
    PayrollError,
    PayrollRunError,
    PayrollValidationError,
)
from app.models.payroll import PayrollRun, Payslip
from app.models.employee import Employee
from app.schemas.payroll import (
    BatchProcessRequest,
    BatchProcessResponse,
    PayrollRunCreate,
    PayrollRunResponse,
    PayslipDetailResponse,
    PayslipResponse,
)
from app.services.payroll_service import PayrollService
from app.services.employee_loader import EmployeeLoader

router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.get(
    "/preview/eligible-count",
    response_model=int,
    summary="Preview eligible employee count for a period",
)
def preview_eligible_count(
    company_id: int = Query(..., description="Company ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    db: Session = Depends(get_db),
):
    """Return how many active employees joined on/before the 15th of the period month."""
    return EmployeeLoader.count_eligible(
        company_id=company_id,
        period_start=period_start,
        period_end=period_end,
        session=db,
    )


@router.get(
    "/preview/eligible-ids",
    response_model=List[int],
    summary="Preview eligible employee IDs for a period",
)
def preview_eligible_ids(
    company_id: int = Query(..., description="Company ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    db: Session = Depends(get_db),
):
    """Return IDs of active employees eligible for payroll in the period."""
    cutoff = EmployeeLoader._cutoff_date(period_start)
    employees = db.query(Employee).filter(
        Employee.company_id == company_id,
        Employee.is_active == True,
        Employee.date_joined <= cutoff,
    ).order_by(Employee.id).all()
    return [e.id for e in employees]


class ApprovalRequest(BaseModel):
    """Request body for approving a payroll run."""

    approved_by: int


# --- Payroll Run Endpoints ---


@router.post(
    "/runs",
    response_model=PayrollRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new payroll run",
)
def create_payroll_run(
    payload: PayrollRunCreate,
    created_by: int = Query(..., description="User ID of the creator"),
    db: Session = Depends(get_db),
):
    """Create a new payroll run in DRAFT status."""
    try:
        payroll_run = PayrollService.create_payroll_run(
            company_id=payload.company_id,
            payroll_period=payload.payroll_period,
            payroll_method=payload.payroll_method,
            tax_method=payload.tax_method,
            created_by=created_by,
            session=db,
        )
        db.commit()
        db.refresh(payroll_run)
        return payroll_run
    except DuplicatePayrollRunError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "DuplicatePayrollRun", "message": e.message, "detail": e.detail},
        )
    except PayrollValidationError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "PayrollValidation", "message": e.message, "detail": e.detail},
        )
    except PayrollError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PayrollError", "message": e.message, "detail": e.detail},
        )


@router.get(
    "/runs",
    response_model=List[PayrollRunResponse],
    summary="List payroll runs for a company",
)
def list_payroll_runs(
    company_id: int = Query(..., description="Company ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List payroll runs filtered by company, with pagination."""
    runs = PayrollService.list_payroll_runs(
        company_id=company_id, session=db, skip=skip, limit=limit
    )
    return runs


@router.get(
    "/runs/{run_id}",
    response_model=PayrollRunResponse,
    summary="Get payroll run detail",
)
def get_payroll_run(run_id: int, db: Session = Depends(get_db)):
    """Retrieve a single payroll run by ID."""
    payroll_run = PayrollService.get_payroll_run(payroll_run_id=run_id, session=db)
    if not payroll_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Payroll run {run_id} not found"},
        )
    return payroll_run


@router.post(
    "/runs/{run_id}/process",
    response_model=PayrollRunResponse,
    summary="Process (calculate) a payroll run",
)
def process_payroll_run(run_id: int, db: Session = Depends(get_db)):
    """Trigger batch payroll calculation for a DRAFT run."""
    try:
        payroll_run = PayrollService.process_payroll_run(
            payroll_run_id=run_id, session=db
        )
        db.commit()
        db.refresh(payroll_run)
        return payroll_run
    except PayrollValidationError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "PayrollValidation", "message": e.message, "detail": e.detail},
        )
    except PayrollRunError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PayrollRunError", "message": e.message, "detail": e.detail},
        )
    except PayrollError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PayrollError", "message": e.message, "detail": e.detail},
        )


@router.post(
    "/runs/{run_id}/process-batch",
    response_model=BatchProcessResponse,
    summary="Process a batch of employees for a payroll run",
)
def process_payroll_batch(
    run_id: int,
    body: BatchProcessRequest,
    db: Session = Depends(get_db),
):
    """Process a subset of employees in chunks to avoid Vercel 10s timeout."""
    try:
        progress = PayrollService.process_payroll_batch(
            payroll_run_id=run_id,
            employee_ids=body.employee_ids,
            finalize=body.finalize,
            session=db,
        )
        db.commit()
        return progress
    except PayrollValidationError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "PayrollValidation", "message": e.message, "detail": e.detail},
        )
    except PayrollRunError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PayrollRunError", "message": e.message, "detail": e.detail},
        )
    except PayrollError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PayrollError", "message": e.message, "detail": e.detail},
        )


@router.post(
    "/runs/{run_id}/approve",
    response_model=PayrollRunResponse,
    summary="Approve a completed payroll run",
)
def approve_payroll_run(
    run_id: int,
    body: ApprovalRequest,
    db: Session = Depends(get_db),
):
    """Approve a COMPLETED payroll run, marking all payslips as approved."""
    try:
        payroll_run = PayrollService.approve_payroll_run(
            payroll_run_id=run_id,
            approved_by=body.approved_by,
            session=db,
        )
        db.commit()
        db.refresh(payroll_run)
        return payroll_run
    except PayrollValidationError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "PayrollValidation", "message": e.message, "detail": e.detail},
        )
    except PayrollRunError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PayrollRunError", "message": e.message, "detail": e.detail},
        )
    except PayrollError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "PayrollError", "message": e.message, "detail": e.detail},
        )


@router.get(
    "/runs/{run_id}/payslips",
    response_model=List[PayslipResponse],
    summary="List payslips for a payroll run",
)
def list_payslips_for_run(
    run_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all payslips belonging to a specific payroll run."""
    # Verify run exists
    payroll_run = db.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    if not payroll_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Payroll run {run_id} not found"},
        )
    payslips = (
        db.query(Payslip)
        .filter(Payslip.payroll_run_id == run_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return payslips


@router.get(
    "/payslips/{payslip_id}",
    response_model=PayslipDetailResponse,
    summary="Get payslip with line items",
)
def get_payslip_detail(payslip_id: int, db: Session = Depends(get_db)):
    """Retrieve a single payslip with its detailed line items."""
    payslip = (
        db.query(Payslip)
        .options(selectinload(Payslip.lines))
        .filter(Payslip.id == payslip_id)
        .first()
    )
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"Payslip {payslip_id} not found"},
        )
    return payslip
