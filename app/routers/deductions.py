"""
Deduction / Iuran configuration API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.salary import DeductionType
from app.schemas.salary import (
    DeductionTypeCreate,
    DeductionTypeResponse,
    DeductionTypeUpdate,
)

router = APIRouter(prefix="/deductions", tags=["Deduction Configuration"])

VALID_CALCULATION_TYPES = {"FIXED", "PERCENTAGE", "FORMULA"}


@router.get(
    "/types",
    response_model=List[DeductionTypeResponse],
    summary="List deduction types",
)
def list_deduction_types(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all deduction types (iuran) for the specified company."""
    return (
        db.query(DeductionType)
        .filter(DeductionType.company_id == company_id)
        .order_by(DeductionType.name)
        .all()
    )


@router.post(
    "/types",
    response_model=DeductionTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create deduction type",
)
def create_deduction_type(payload: DeductionTypeCreate, db: Session = Depends(get_db)):
    """Create a new deduction type for a company."""
    if payload.calculation_type not in VALID_CALCULATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"calculation_type must be one of {sorted(VALID_CALCULATION_TYPES)}",
            },
        )

    existing = (
        db.query(DeductionType)
        .filter(
            DeductionType.company_id == payload.company_id,
            DeductionType.code == payload.code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate",
                "message": f"Deduction code '{payload.code}' already exists for this company",
            },
        )

    deduction = DeductionType(**payload.model_dump())
    db.add(deduction)
    db.commit()
    db.refresh(deduction)
    return deduction


@router.patch(
    "/types/{deduction_type_id}",
    response_model=DeductionTypeResponse,
    summary="Update deduction type",
)
def update_deduction_type(
    deduction_type_id: int,
    payload: DeductionTypeUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a deduction type."""
    deduction = (
        db.query(DeductionType)
        .filter(DeductionType.id == deduction_type_id)
        .first()
    )
    if not deduction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Deduction type {deduction_type_id} not found",
            },
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "calculation_type" in update_data:
        if update_data["calculation_type"] not in VALID_CALCULATION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": f"calculation_type must be one of {sorted(VALID_CALCULATION_TYPES)}",
                },
            )

    if "code" in update_data:
        existing = (
            db.query(DeductionType)
            .filter(
                DeductionType.company_id == deduction.company_id,
                DeductionType.code == update_data["code"],
                DeductionType.id != deduction_type_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Duplicate",
                    "message": f"Deduction code '{update_data['code']}' already exists for this company",
                },
            )

    for field, value in update_data.items():
        setattr(deduction, field, value)

    db.commit()
    db.refresh(deduction)
    return deduction


@router.delete(
    "/types/{deduction_type_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete deduction type",
)
def delete_deduction_type(deduction_type_id: int, db: Session = Depends(get_db)):
    """Delete a deduction type."""
    deduction = (
        db.query(DeductionType)
        .filter(DeductionType.id == deduction_type_id)
        .first()
    )
    if not deduction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Deduction type {deduction_type_id} not found",
            },
        )

    db.delete(deduction)
    db.commit()
    return {"message": "Deduction type deleted"}
