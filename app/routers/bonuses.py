"""
Bonus management API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bonus import Bonus, BonusType
from app.models.employee import Employee
from app.schemas.bonus import (
    BonusCreate,
    BonusResponse,
    BonusUpdate,
    BonusTypeCreate,
    BonusTypeResponse,
    BonusTypeUpdate,
)

router = APIRouter(prefix="/bonuses", tags=["Bonus Management"])

VALID_APPROVAL_STATUS = {"PENDING", "APPROVED", "REJECTED"}


# ─── Bonus Types ─────────────────────────────────────────────────────────────


@router.get(
    "/types",
    response_model=List[BonusTypeResponse],
    summary="List bonus types",
)
def list_bonus_types(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all bonus types for the specified company."""
    return (
        db.query(BonusType)
        .filter(BonusType.company_id == company_id)
        .order_by(BonusType.name)
        .all()
    )


@router.post(
    "/types",
    response_model=BonusTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create bonus type",
)
def create_bonus_type(payload: BonusTypeCreate, db: Session = Depends(get_db)):
    """Create a new bonus type for a company."""
    existing = (
        db.query(BonusType)
        .filter(
            BonusType.company_id == payload.company_id,
            BonusType.code == payload.code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate",
                "message": f"Bonus code '{payload.code}' already exists for this company",
            },
        )

    bonus_type = BonusType(**payload.model_dump())
    db.add(bonus_type)
    db.commit()
    db.refresh(bonus_type)
    return bonus_type


@router.patch(
    "/types/{bonus_type_id}",
    response_model=BonusTypeResponse,
    summary="Update bonus type",
)
def update_bonus_type(
    bonus_type_id: int,
    payload: BonusTypeUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a bonus type."""
    bonus_type = db.query(BonusType).filter(BonusType.id == bonus_type_id).first()
    if not bonus_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Bonus type not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "code" in update_data:
        existing = (
            db.query(BonusType)
            .filter(
                BonusType.company_id == bonus_type.company_id,
                BonusType.code == update_data["code"],
                BonusType.id != bonus_type_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Duplicate",
                    "message": f"Bonus code '{update_data['code']}' already exists",
                },
            )

    for field, value in update_data.items():
        setattr(bonus_type, field, value)

    db.commit()
    db.refresh(bonus_type)
    return bonus_type


@router.delete(
    "/types/{bonus_type_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete bonus type",
)
def delete_bonus_type(bonus_type_id: int, db: Session = Depends(get_db)):
    """Delete a bonus type. Fails if it is in use."""
    bonus_type = db.query(BonusType).filter(BonusType.id == bonus_type_id).first()
    if not bonus_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Bonus type not found"},
        )

    count = db.query(Bonus).filter(Bonus.bonus_type_id == bonus_type_id).count()
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InUse",
                "message": f"Cannot delete: {count} bonus record(s) use this type.",
            },
        )

    db.delete(bonus_type)
    db.commit()
    return {"message": "Bonus type deleted"}


# ─── Bonus Records ───────────────────────────────────────────────────────────


def _build_bonus_response(db: Session, bonus: Bonus) -> BonusResponse:
    employee = db.query(Employee).filter(Employee.id == bonus.employee_id).first()
    bonus_type = (
        db.query(BonusType).filter(BonusType.id == bonus.bonus_type_id).first()
    )
    return BonusResponse(
        id=bonus.id,
        employee_id=bonus.employee_id,
        employee_name=(
            f"{employee.first_name} {employee.last_name or ''}".strip()
            if employee
            else f"Employee #{bonus.employee_id}"
        ),
        bonus_type_id=bonus.bonus_type_id,
        bonus_type_name=bonus_type.name if bonus_type else f"Type #{bonus.bonus_type_id}",
        amount=bonus.amount,
        bonus_date=bonus.bonus_date,
        description=bonus.description,
        approval_status=bonus.approval_status,
        approved_by=bonus.approved_by,
        approval_date=bonus.approval_date,
        payroll_run_id=bonus.payroll_run_id,
        is_processed=bonus.is_processed,
        created_at=bonus.created_at,
        updated_at=bonus.updated_at,
    )


@router.get(
    "",
    response_model=List[BonusResponse],
    summary="List bonus records",
)
def list_bonuses(
    company_id: int = Query(..., description="Company ID"),
    employee_id: int = Query(None, description="Filter by employee ID"),
    status: str = Query(None, description="Filter by approval status"),
    db: Session = Depends(get_db),
):
    """List bonus records for a company, optionally filtered."""
    query = db.query(Bonus).join(Employee).filter(Employee.company_id == company_id)

    if employee_id:
        query = query.filter(Bonus.employee_id == employee_id)
    if status:
        query = query.filter(Bonus.approval_status == status)

    bonuses = query.order_by(Bonus.bonus_date.desc()).all()
    return [_build_bonus_response(db, b) for b in bonuses]


@router.post(
    "",
    response_model=BonusResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create bonus record",
)
def create_bonus(payload: BonusCreate, db: Session = Depends(get_db)):
    """Create a new bonus record for an employee."""
    employee = db.query(Employee).filter(Employee.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidValue", "message": "Employee not found"},
        )

    bonus_type = (
        db.query(BonusType).filter(BonusType.id == payload.bonus_type_id).first()
    )
    if not bonus_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidValue", "message": "Bonus type not found"},
        )

    bonus = Bonus(
        employee_id=payload.employee_id,
        bonus_type_id=payload.bonus_type_id,
        amount=payload.amount,
        bonus_date=payload.bonus_date,
        description=payload.description,
        approval_status="PENDING",
    )
    db.add(bonus)
    db.commit()
    db.refresh(bonus)
    return _build_bonus_response(db, bonus)


@router.patch(
    "/{bonus_id}",
    response_model=BonusResponse,
    summary="Update bonus record",
)
def update_bonus(
    bonus_id: int,
    payload: BonusUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a bonus record, including approval status."""
    bonus = db.query(Bonus).filter(Bonus.id == bonus_id).first()
    if not bonus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Bonus not found"},
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
        if bonus.is_processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidState",
                    "message": "Cannot change approval status of a processed bonus",
                },
            )

    if "bonus_type_id" in update_data:
        bonus_type = (
            db.query(BonusType)
            .filter(BonusType.id == update_data["bonus_type_id"])
            .first()
        )
        if not bonus_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "InvalidValue", "message": "Bonus type not found"},
            )

    for field, value in update_data.items():
        setattr(bonus, field, value)

    db.commit()
    db.refresh(bonus)
    return _build_bonus_response(db, bonus)


@router.delete(
    "/{bonus_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete bonus record",
)
def delete_bonus(bonus_id: int, db: Session = Depends(get_db)):
    """Delete a bonus record."""
    bonus = db.query(Bonus).filter(Bonus.id == bonus_id).first()
    if not bonus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Bonus not found"},
        )

    if bonus.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidState",
                "message": "Cannot delete a processed bonus",
            },
        )

    db.delete(bonus)
    db.commit()
    return {"message": "Bonus deleted"}
