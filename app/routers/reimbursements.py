"""
Reimbursement management API endpoints.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bonus import Reimbursement, ReimbursementType
from app.models.employee import Employee
from app.schemas.bonus import (
    ReimbursementCreate,
    ReimbursementResponse,
    ReimbursementUpdate,
    ReimbursementTypeCreate,
    ReimbursementTypeResponse,
    ReimbursementTypeUpdate,
)

router = APIRouter(prefix="/reimbursements", tags=["Reimbursement Management"])

VALID_APPROVAL_STATUS = {"PENDING", "APPROVED", "REJECTED"}


# ─── Reimbursement Types ─────────────────────────────────────────────────────


@router.get(
    "/types",
    response_model=List[ReimbursementTypeResponse],
    summary="List reimbursement types",
)
def list_reimbursement_types(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all reimbursement types for the specified company."""
    return (
        db.query(ReimbursementType)
        .filter(ReimbursementType.company_id == company_id)
        .order_by(ReimbursementType.name)
        .all()
    )


@router.post(
    "/types",
    response_model=ReimbursementTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create reimbursement type",
)
def create_reimbursement_type(
    payload: ReimbursementTypeCreate, db: Session = Depends(get_db)
):
    """Create a new reimbursement type for a company."""
    existing = (
        db.query(ReimbursementType)
        .filter(
            ReimbursementType.company_id == payload.company_id,
            ReimbursementType.code == payload.code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate",
                "message": f"Reimbursement code '{payload.code}' already exists for this company",
            },
        )

    reimbursement_type = ReimbursementType(**payload.model_dump())
    db.add(reimbursement_type)
    db.commit()
    db.refresh(reimbursement_type)
    return reimbursement_type


@router.patch(
    "/types/{reimbursement_type_id}",
    response_model=ReimbursementTypeResponse,
    summary="Update reimbursement type",
)
def update_reimbursement_type(
    reimbursement_type_id: int,
    payload: ReimbursementTypeUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a reimbursement type."""
    reimbursement_type = (
        db.query(ReimbursementType)
        .filter(ReimbursementType.id == reimbursement_type_id)
        .first()
    )
    if not reimbursement_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Reimbursement type not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "code" in update_data:
        existing = (
            db.query(ReimbursementType)
            .filter(
                ReimbursementType.company_id == reimbursement_type.company_id,
                ReimbursementType.code == update_data["code"],
                ReimbursementType.id != reimbursement_type_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Duplicate",
                    "message": f"Reimbursement code '{update_data['code']}' already exists",
                },
            )

    for field, value in update_data.items():
        setattr(reimbursement_type, field, value)

    db.commit()
    db.refresh(reimbursement_type)
    return reimbursement_type


@router.delete(
    "/types/{reimbursement_type_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete reimbursement type",
)
def delete_reimbursement_type(
    reimbursement_type_id: int, db: Session = Depends(get_db)
):
    """Delete a reimbursement type. Fails if it is in use."""
    reimbursement_type = (
        db.query(ReimbursementType)
        .filter(ReimbursementType.id == reimbursement_type_id)
        .first()
    )
    if not reimbursement_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Reimbursement type not found"},
        )

    count = (
        db.query(Reimbursement)
        .filter(Reimbursement.reimbursement_type_id == reimbursement_type_id)
        .count()
    )
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InUse",
                "message": f"Cannot delete: {count} reimbursement record(s) use this type.",
            },
        )

    db.delete(reimbursement_type)
    db.commit()
    return {"message": "Reimbursement type deleted"}


# ─── Reimbursement Claims ────────────────────────────────────────────────────


def _build_reimbursement_response(
    db: Session, reimbursement: Reimbursement
) -> ReimbursementResponse:
    employee = (
        db.query(Employee).filter(Employee.id == reimbursement.employee_id).first()
    )
    reimbursement_type = (
        db.query(ReimbursementType)
        .filter(ReimbursementType.id == reimbursement.reimbursement_type_id)
        .first()
    )
    return ReimbursementResponse(
        id=reimbursement.id,
        employee_id=reimbursement.employee_id,
        employee_name=(
            f"{employee.first_name} {employee.last_name or ''}".strip()
            if employee
            else f"Employee #{reimbursement.employee_id}"
        ),
        reimbursement_type_id=reimbursement.reimbursement_type_id,
        reimbursement_type_name=(
            reimbursement_type.name
            if reimbursement_type
            else f"Type #{reimbursement.reimbursement_type_id}"
        ),
        claim_amount=reimbursement.claim_amount,
        approved_amount=reimbursement.approved_amount,
        claim_date=reimbursement.claim_date,
        expense_date=reimbursement.expense_date,
        description=reimbursement.description,
        receipt_path=reimbursement.receipt_path,
        approval_status=reimbursement.approval_status,
        approved_by=reimbursement.approved_by,
        approval_date=reimbursement.approval_date,
        payroll_run_id=reimbursement.payroll_run_id,
        is_processed=reimbursement.is_processed,
        created_at=reimbursement.created_at,
        updated_at=reimbursement.updated_at,
    )


@router.get(
    "",
    response_model=List[ReimbursementResponse],
    summary="List reimbursement claims",
)
def list_reimbursements(
    company_id: int = Query(..., description="Company ID"),
    employee_id: int = Query(None, description="Filter by employee ID"),
    status: str = Query(None, description="Filter by approval status"),
    db: Session = Depends(get_db),
):
    """List reimbursement claims for a company, optionally filtered."""
    query = (
        db.query(Reimbursement)
        .join(Employee)
        .filter(Employee.company_id == company_id)
    )

    if employee_id:
        query = query.filter(Reimbursement.employee_id == employee_id)
    if status:
        query = query.filter(Reimbursement.approval_status == status)

    reimbursements = query.order_by(Reimbursement.claim_date.desc()).all()
    return [_build_reimbursement_response(db, r) for r in reimbursements]


@router.post(
    "",
    response_model=ReimbursementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create reimbursement claim",
)
def create_reimbursement(
    payload: ReimbursementCreate, db: Session = Depends(get_db)
):
    """Create a new reimbursement claim for an employee."""
    employee = (
        db.query(Employee).filter(Employee.id == payload.employee_id).first()
    )
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidValue", "message": "Employee not found"},
        )

    reimbursement_type = (
        db.query(ReimbursementType)
        .filter(ReimbursementType.id == payload.reimbursement_type_id)
        .first()
    )
    if not reimbursement_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": "Reimbursement type not found",
            },
        )

    if (
        reimbursement_type.max_amount is not None
        and payload.claim_amount > reimbursement_type.max_amount
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ExceedsLimit",
                "message": (
                    f"Claim amount exceeds maximum allowed for this type "
                    f"(Rp {reimbursement_type.max_amount:,.0f})"
                ),
            },
        )

    reimbursement = Reimbursement(
        employee_id=payload.employee_id,
        reimbursement_type_id=payload.reimbursement_type_id,
        claim_amount=payload.claim_amount,
        claim_date=payload.claim_date,
        expense_date=payload.expense_date,
        description=payload.description,
        receipt_path=payload.receipt_path,
        approval_status="PENDING",
    )
    db.add(reimbursement)
    db.commit()
    db.refresh(reimbursement)
    return _build_reimbursement_response(db, reimbursement)


@router.patch(
    "/{reimbursement_id}",
    response_model=ReimbursementResponse,
    summary="Update reimbursement claim",
)
def update_reimbursement(
    reimbursement_id: int,
    payload: ReimbursementUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a reimbursement claim, including approval status."""
    reimbursement = (
        db.query(Reimbursement)
        .filter(Reimbursement.id == reimbursement_id)
        .first()
    )
    if not reimbursement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Reimbursement not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "approval_status" in update_data:
        if update_data["approval_status"] not in VALID_APPROVAL_STATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": f"approval_status must be one of {sorted(VALID_APPROVAL_STATUS)}",
                },
            )
        if reimbursement.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidState",
                    "message": "Cannot change approval status of a processed reimbursement",
                },
            )
        if update_data["approval_status"] == "APPROVED":
            update_data["approved_amount"] = (
                update_data.get("approved_amount")
                or reimbursement.approved_amount
                or reimbursement.claim_amount
            )
            update_data["approval_date"] = datetime.now()

    if "reimbursement_type_id" in update_data:
        reimbursement_type = (
            db.query(ReimbursementType)
            .filter(ReimbursementType.id == update_data["reimbursement_type_id"])
            .first()
        )
        if not reimbursement_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": "Reimbursement type not found",
                },
            )

    for field, value in update_data.items():
        setattr(reimbursement, field, value)

    db.commit()
    db.refresh(reimbursement)
    return _build_reimbursement_response(db, reimbursement)


@router.delete(
    "/{reimbursement_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete reimbursement claim",
)
def delete_reimbursement(
    reimbursement_id: int, db: Session = Depends(get_db)
):
    """Delete a reimbursement claim."""
    reimbursement = (
        db.query(Reimbursement)
        .filter(Reimbursement.id == reimbursement_id)
        .first()
    )
    if not reimbursement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Reimbursement not found"},
        )

    if reimbursement.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidState",
                "message": "Cannot delete a processed reimbursement",
            },
        )

    db.delete(reimbursement)
    db.commit()
    return {"message": "Reimbursement deleted"}
