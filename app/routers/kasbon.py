"""
Kasbon (employee loan / cash advance) management API endpoints.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.kasbon import KasbonInstallment, KasbonRequest
from app.schemas.kasbon import (
    KasbonCreate,
    KasbonResponse,
    KasbonStatusUpdate,
    KasbonUpdate,
)

router = APIRouter(prefix="/kasbon", tags=["Kasbon Management"])

VALID_STATUS = {"PENDING", "APPROVED", "DISBURSED", "COMPLETED", "REJECTED"}


def _generate_installments(kasbon: KasbonRequest) -> None:
    """Generate installment schedule when a kasbon is disbursed."""
    # Clear any existing installments to allow regeneration
    for inst in kasbon.installments:
        if not inst.is_paid:
            inst.payroll_run_id = None

    # Use disbursement_date as the base due date; if not set, use request_date
    base_date = kasbon.disbursement_date or kasbon.request_date
    for i in range(1, kasbon.number_of_installments + 1):
        # Simple monthly due dates
        due_month = base_date.month + i - 1
        due_year = base_date.year
        while due_month > 12:
            due_month -= 12
            due_year += 1
        # Use last day of the month safely
        try:
            due_date = date(due_year, due_month, base_date.day)
        except ValueError:
            # February / shorter month fallback
            import calendar

            last_day = calendar.monthrange(due_year, due_month)[1]
            due_date = date(due_year, due_month, last_day)

        installment = KasbonInstallment(
            kasbon_request_id=kasbon.id,
            installment_number=i,
            amount=kasbon.installment_amount,
            due_date=due_date,
            is_paid=False,
        )
        kasbon.installments.append(installment)


def _build_kasbon_response(db: Session, kasbon: KasbonRequest) -> KasbonResponse:
    employee = db.query(Employee).filter(Employee.id == kasbon.employee_id).first()

    installments = [
        {
            "id": inst.id,
            "installment_number": inst.installment_number,
            "amount": inst.amount,
            "due_date": inst.due_date,
            "is_paid": inst.is_paid,
            "paid_date": inst.paid_date,
            "payroll_run_id": inst.payroll_run_id,
        }
        for inst in sorted(kasbon.installments, key=lambda x: x.installment_number)
    ]

    total_paid = sum(
        inst.amount for inst in kasbon.installments if inst.is_paid
    )
    remaining_balance = kasbon.principal_amount - total_paid

    return KasbonResponse(
        id=kasbon.id,
        employee_id=kasbon.employee_id,
        employee_name=(
            f"{employee.first_name} {employee.last_name or ''}".strip()
            if employee
            else f"Employee #{kasbon.employee_id}"
        ),
        kasbon_number=kasbon.kasbon_number,
        principal_amount=kasbon.principal_amount,
        purpose=kasbon.purpose,
        request_date=kasbon.request_date,
        approval_date=kasbon.approval_date,
        disbursement_date=kasbon.disbursement_date,
        number_of_installments=kasbon.number_of_installments,
        installment_amount=kasbon.installment_amount,
        status=kasbon.status,
        approved_by=kasbon.approved_by,
        notes=kasbon.notes,
        created_at=kasbon.created_at,
        updated_at=kasbon.updated_at,
        installments=installments,
        total_paid=total_paid,
        remaining_balance=remaining_balance,
    )


@router.get(
    "",
    response_model=List[KasbonResponse],
    summary="List kasbon requests",
)
def list_kasbon(
    company_id: int = Query(..., description="Company ID"),
    employee_id: int = Query(None, description="Filter by employee ID"),
    status: str = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """List kasbon requests for a company, optionally filtered."""
    query = (
        db.query(KasbonRequest)
        .join(Employee)
        .filter(Employee.company_id == company_id)
    )

    if employee_id:
        query = query.filter(KasbonRequest.employee_id == employee_id)
    if status:
        query = query.filter(KasbonRequest.status == status)

    kasbon_list = query.order_by(KasbonRequest.request_date.desc()).all()
    return [_build_kasbon_response(db, k) for k in kasbon_list]


@router.post(
    "",
    response_model=KasbonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create kasbon request",
)
def create_kasbon(payload: KasbonCreate, db: Session = Depends(get_db)):
    """Create a new employee loan / cash advance request."""
    employee = (
        db.query(Employee).filter(Employee.id == payload.employee_id).first()
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidValue", "message": "Employee not found"},
        )

    existing = (
        db.query(KasbonRequest)
        .filter(KasbonRequest.kasbon_number == payload.kasbon_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate",
                "message": f"Kasbon number '{payload.kasbon_number}' already exists",
            },
        )

    # Validate installment consistency
    expected = payload.principal_amount / Decimal(payload.number_of_installments)
    if payload.installment_amount != expected:
        # Allow rounding differences up to 1 unit of currency
        diff = abs(payload.installment_amount - expected)
        if diff > Decimal("1"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": (
                        f"Installment amount should be approximately "
                        f"Rp {expected:,.0f} for {payload.number_of_installments} installments"
                    ),
                },
            )

    kasbon = KasbonRequest(
        employee_id=payload.employee_id,
        kasbon_number=payload.kasbon_number,
        principal_amount=payload.principal_amount,
        purpose=payload.purpose,
        request_date=payload.request_date,
        number_of_installments=payload.number_of_installments,
        installment_amount=payload.installment_amount,
        status="PENDING",
        notes=payload.notes,
    )
    db.add(kasbon)
    db.commit()
    db.refresh(kasbon)
    return _build_kasbon_response(db, kasbon)


@router.patch(
    "/{kasbon_id}",
    response_model=KasbonResponse,
    summary="Update kasbon request",
)
def update_kasbon(
    kasbon_id: int,
    payload: KasbonUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a kasbon request before approval/disbursement."""
    kasbon = (
        db.query(KasbonRequest).filter(KasbonRequest.id == kasbon_id).first()
    )
    if not kasbon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Kasbon not found"},
        )

    if kasbon.status in {"DISBURSED", "COMPLETED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidState",
                "message": "Cannot update a disbursed or completed kasbon",
            },
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "status" in update_data:
        if update_data["status"] not in VALID_STATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": f"status must be one of {sorted(VALID_STATUS)}",
                },
            )

    if "kasbon_number" in update_data:
        existing = (
            db.query(KasbonRequest)
            .filter(
                KasbonRequest.kasbon_number == update_data["kasbon_number"],
                KasbonRequest.id != kasbon_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Duplicate",
                    "message": f"Kasbon number '{update_data['kasbon_number']}' already exists",
                },
            )

    for field, value in update_data.items():
        setattr(kasbon, field, value)

    db.commit()
    db.refresh(kasbon)
    return _build_kasbon_response(db, kasbon)


@router.patch(
    "/{kasbon_id}/status",
    response_model=KasbonResponse,
    summary="Update kasbon status (approve/reject/disburse)",
)
def update_kasbon_status(
    kasbon_id: int,
    payload: KasbonStatusUpdate,
    db: Session = Depends(get_db),
):
    """Approve, reject, or disburse a kasbon request."""
    kasbon = (
        db.query(KasbonRequest).filter(KasbonRequest.id == kasbon_id).first()
    )
    if not kasbon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Kasbon not found"},
        )

    if payload.status not in VALID_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"status must be one of {sorted(VALID_STATUS)}",
            },
        )

    new_status = payload.status

    if new_status == "APPROVED":
        if kasbon.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidState",
                    "message": "Only PENDING kasbon can be approved",
                },
            )
        kasbon.status = "APPROVED"
        kasbon.approved_by = payload.approved_by
        kasbon.approval_date = date.today()

    elif new_status == "REJECTED":
        if kasbon.status in {"DISBURSED", "COMPLETED"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidState",
                    "message": "Cannot reject a disbursed or completed kasbon",
                },
            )
        kasbon.status = "REJECTED"
        kasbon.approved_by = payload.approved_by
        kasbon.approval_date = date.today()

    elif new_status == "DISBURSED":
        if kasbon.status != "APPROVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidState",
                    "message": "Only APPROVED kasbon can be disbursed",
                },
            )
        kasbon.status = "DISBURSED"
        kasbon.disbursement_date = date.today()
        _generate_installments(kasbon)

    elif new_status == "COMPLETED":
        if kasbon.status != "DISBURSED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidState",
                    "message": "Only DISBURSED kasbon can be marked completed",
                },
            )
        kasbon.status = "COMPLETED"

    db.commit()
    db.refresh(kasbon)
    return _build_kasbon_response(db, kasbon)


@router.delete(
    "/{kasbon_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete kasbon request",
)
def delete_kasbon(kasbon_id: int, db: Session = Depends(get_db)):
    """Delete a kasbon request. Only allowed before disbursement."""
    kasbon = (
        db.query(KasbonRequest).filter(KasbonRequest.id == kasbon_id).first()
    )
    if not kasbon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Kasbon not found"},
        )

    if kasbon.status in {"DISBURSED", "COMPLETED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidState",
                "message": "Cannot delete a disbursed or completed kasbon",
            },
        )

    db.delete(kasbon)
    db.commit()
    return {"message": "Kasbon deleted"}
