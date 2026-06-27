"""
Tunjangan Hari Raya (THR) API endpoints.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bonus import THRConfig, THRRecord
from app.models.employee import Employee
from app.schemas.bonus import (
    THRCreate,
    THRResponse,
    THRUpdate,
    THRCalculateRequest,
    THRConfigResponse,
    THRConfigUpdate,
)

router = APIRouter(prefix="/thr", tags=["THR Management"])

VALID_HOLIDAYS = {"IDUL_FITRI", "CHRISTMAS", "NYEPI", "WAISAK"}
VALID_STATUS = {"DRAFT", "APPROVED", "PAID"}


def _months_between(start: date, end: date, round_up_partial: bool = False) -> int:
    """Return full months between two dates.

    If round_up_partial is True, any day past the start day in the end month
    counts as an additional full month.
    """
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if round_up_partial and end.day > start.day:
        months += 1
    return months


def _calculate_thr_amount(
    base_salary: Decimal,
    tenure_months: int,
    full_tenure_months: int,
    min_tenure_months: int,
) -> tuple[Decimal, str]:
    """Calculate THR amount using configurable tenure thresholds.

    - tenure >= full_tenure_months: 1 month base salary
    - min_tenure_months <= tenure < full_tenure_months: prorated (tenure/12)
    - tenure < min_tenure_months: no THR
    """
    if tenure_months >= full_tenure_months:
        return base_salary, "BASE_SALARY"
    if tenure_months >= min_tenure_months:
        return round(base_salary * Decimal(tenure_months) / Decimal(12), 2), "PRORATED"
    return Decimal("0"), "PRORATED"


HOLIDAY_TO_RELIGION = {
    "IDUL_FITRI": {"Islam"},
    "CHRISTMAS": {"Protestan", "Katolik"},
    "NYEPI": {"Hindu"},
    "WAISAK": {"Buddha"},
}


def _religion_matches_holiday(religion: Optional[str], holiday: str) -> bool:
    """Check whether an employee religion matches a religious holiday."""
    if not religion:
        return False
    allowed = HOLIDAY_TO_RELIGION.get(holiday, set())
    return religion in allowed


def _get_or_create_thr_config(db: Session, company_id: int) -> THRConfig:
    config = db.query(THRConfig).filter(THRConfig.company_id == company_id).first()
    if not config:
        config = THRConfig(
            company_id=company_id,
            payment_mode="BY_RELIGION",
            unified_holiday="IDUL_FITRI",
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def _build_thr_response(db: Session, thr: THRRecord) -> THRResponse:
    employee = db.query(Employee).filter(Employee.id == thr.employee_id).first()
    return THRResponse(
        id=thr.id,
        company_id=thr.company_id,
        employee_id=thr.employee_id,
        employee_name=(
            f"{employee.first_name} {employee.last_name or ''}".strip()
            if employee
            else f"Employee #{thr.employee_id}"
        ),
        employee_religion=employee.religion if employee else None,
        thr_year=thr.thr_year,
        religious_holiday=thr.religious_holiday,
        amount=thr.amount,
        thr_date=thr.thr_date,
        calculation_basis=thr.calculation_basis,
        tenure_months=thr.tenure_months,
        status=thr.status,
        description=thr.description,
        payroll_run_id=thr.payroll_run_id,
        is_processed=thr.is_processed,
        created_at=thr.created_at,
        updated_at=thr.updated_at,
    )


@router.get(
    "/config",
    response_model=THRConfigResponse,
    summary="Get company THR configuration",
)
def get_thr_config(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """Return company THR configuration, creating defaults if missing."""
    config = _get_or_create_thr_config(db, company_id)
    return config


@router.put(
    "/config",
    response_model=THRConfigResponse,
    summary="Update company THR configuration",
)
def update_thr_config(
    payload: THRConfigUpdate,
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """Update company THR configuration."""
    if payload.payment_mode not in {"BY_RELIGION", "UNIFIED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": "payment_mode must be BY_RELIGION or UNIFIED",
            },
        )
    if payload.unified_holiday not in VALID_HOLIDAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"unified_holiday must be one of {sorted(VALID_HOLIDAYS)}",
            },
        )
    if payload.full_tenure_months < payload.min_tenure_months:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": "full_tenure_months must be >= min_tenure_months",
            },
        )

    config = _get_or_create_thr_config(db, company_id)
    config.payment_mode = payload.payment_mode
    config.unified_holiday = payload.unified_holiday
    config.full_tenure_months = payload.full_tenure_months
    config.min_tenure_months = payload.min_tenure_months
    config.prorate_partial_months = payload.prorate_partial_months
    config.is_active = payload.is_active
    db.commit()
    db.refresh(config)
    return config


@router.get(
    "",
    response_model=List[THRResponse],
    summary="List THR records",
)
def list_thr_records(
    company_id: int = Query(..., description="Company ID"),
    thr_year: int = Query(None, description="Filter by THR year"),
    religious_holiday: str = Query(None, description="Filter by religious holiday"),
    db: Session = Depends(get_db),
):
    """List THR records for a company, optionally filtered."""
    query = db.query(THRRecord).join(Employee).filter(Employee.company_id == company_id)

    if thr_year:
        query = query.filter(THRRecord.thr_year == thr_year)
    if religious_holiday:
        query = query.filter(THRRecord.religious_holiday == religious_holiday)

    records = query.order_by(THRRecord.thr_date.desc()).all()
    return [_build_thr_response(db, r) for r in records]


@router.post(
    "/calculate",
    response_model=List[THRResponse],
    summary="Bulk calculate THR records",
)
def calculate_thr(payload: THRCalculateRequest, db: Session = Depends(get_db)):
    """Bulk calculate THR for active employees based on company configuration.

    - BY_RELIGION mode: only employees whose religion matches the requested
      holiday are calculated.
    - UNIFIED mode: all active employees are calculated for the requested
      holiday (typically the configured unified_holiday).
    """
    if payload.religious_holiday not in VALID_HOLIDAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"religious_holiday must be one of {sorted(VALID_HOLIDAYS)}",
            },
        )

    config = _get_or_create_thr_config(db, payload.company_id)

    employees = db.query(Employee).filter(
        Employee.company_id == payload.company_id,
        Employee.is_active == True,
    ).all()

    created_records = []
    for emp in employees:
        # In BY_RELIGION mode skip employees whose religion does not match
        if config.payment_mode == "BY_RELIGION" and not _religion_matches_holiday(
            emp.religion, payload.religious_holiday
        ):
            continue

        if not emp.date_joined or not emp.base_salary or emp.base_salary <= 0:
            continue

        tenure_months = _months_between(
            emp.date_joined, payload.reference_date, config.prorate_partial_months
        )
        amount, basis = _calculate_thr_amount(
            emp.base_salary,
            tenure_months,
            config.full_tenure_months,
            config.min_tenure_months,
        )

        if amount <= 0:
            continue

        existing = (
            db.query(THRRecord)
            .filter(
                THRRecord.employee_id == emp.id,
                THRRecord.thr_year == payload.thr_year,
                THRRecord.religious_holiday == payload.religious_holiday,
            )
            .first()
        )
        if existing:
            if existing.is_processed:
                continue
            existing.amount = amount
            existing.calculation_basis = basis
            existing.tenure_months = tenure_months
            existing.thr_date = payload.reference_date
        else:
            record = THRRecord(
                company_id=payload.company_id,
                employee_id=emp.id,
                thr_year=payload.thr_year,
                religious_holiday=payload.religious_holiday,
                amount=amount,
                thr_date=payload.reference_date,
                calculation_basis=basis,
                tenure_months=tenure_months,
                status="DRAFT",
            )
            db.add(record)
            created_records.append(record)

    db.commit()

    # Refresh all records for this company/year/holiday
    records = (
        db.query(THRRecord)
        .join(Employee)
        .filter(
            Employee.company_id == payload.company_id,
            THRRecord.thr_year == payload.thr_year,
            THRRecord.religious_holiday == payload.religious_holiday,
        )
        .all()
    )
    return [_build_thr_response(db, r) for r in records]


@router.post(
    "",
    response_model=THRResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create THR record",
)
def create_thr(payload: THRCreate, db: Session = Depends(get_db)):
    """Create a manual THR record."""
    if payload.religious_holiday not in VALID_HOLIDAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"religious_holiday must be one of {sorted(VALID_HOLIDAYS)}",
            },
        )

    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidValue", "message": "Employee not found"},
        )

    existing = (
        db.query(THRRecord)
        .filter(
            THRRecord.employee_id == payload.employee_id,
            THRRecord.thr_year == payload.thr_year,
            THRRecord.religious_holiday == payload.religious_holiday,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Duplicate",
                "message": "THR record already exists for this employee, year, and holiday",
            },
        )

    record = THRRecord(
        company_id=employee.company_id,
        **payload.model_dump(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _build_thr_response(db, record)


@router.patch(
    "/{thr_id}",
    response_model=THRResponse,
    summary="Update THR record",
)
def update_thr(
    thr_id: int,
    payload: THRUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a THR record."""
    record = db.query(THRRecord).filter(THRRecord.id == thr_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "THR record not found"},
        )

    if record.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidState", "message": "Cannot update a processed THR record"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "status" in update_data and update_data["status"] not in VALID_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"status must be one of {sorted(VALID_STATUS)}",
            },
        )

    for field, value in update_data.items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return _build_thr_response(db, record)


@router.delete(
    "/{thr_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete THR record",
)
def delete_thr(thr_id: int, db: Session = Depends(get_db)):
    """Delete a THR record."""
    record = db.query(THRRecord).filter(THRRecord.id == thr_id).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "THR record not found"},
        )

    if record.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidState", "message": "Cannot delete a processed THR record"},
        )

    db.delete(record)
    db.commit()
    return {"message": "THR record deleted"}
