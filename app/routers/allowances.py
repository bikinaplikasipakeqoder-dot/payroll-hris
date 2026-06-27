"""
Allowance configuration API endpoints.
"""

from typing import List, Type

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Department, Position
from app.models.salary import (
    AllowanceType,
    EmployeeAllowance,
    AllowanceGradeMatrix,
    AllowancePositionMatrix,
    AllowanceDepartmentMatrix,
    Grade,
)
from app.schemas.salary import (
    AllowanceMatrixCreate,
    AllowanceMatrixResponse,
    AllowanceMatrixUpdate,
    AllowanceTypeCreate,
    AllowanceTypeResponse,
    AllowanceTypeUpdate,
)

router = APIRouter(prefix="/allowances", tags=["Allowance Configuration"])

VALID_CALCULATION_TYPES = {"FIXED", "PERCENTAGE", "FORMULA"}
VALID_AMOUNT_BASIS = {"UNIVERSAL", "GRADE", "POSITION", "DEPARTMENT", "INDIVIDUAL"}
VALID_MATRIX_BASIS = {"GRADE", "POSITION", "DEPARTMENT"}

MATRIX_MODELS = {
    "GRADE": AllowanceGradeMatrix,
    "POSITION": AllowancePositionMatrix,
    "DEPARTMENT": AllowanceDepartmentMatrix,
}

ENTITY_MODELS = {
    "GRADE": Grade,
    "POSITION": Position,
    "DEPARTMENT": Department,
}

ENTITY_NAME_FIELDS = {
    "GRADE": "grade_name",
    "POSITION": "name",
    "DEPARTMENT": "name",
}


@router.get(
    "/types",
    response_model=List[AllowanceTypeResponse],
    summary="List allowance types",
)
def list_allowance_types(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all allowance types for the specified company."""
    return (
        db.query(AllowanceType)
        .filter(AllowanceType.company_id == company_id)
        .order_by(AllowanceType.sort_order, AllowanceType.name)
        .all()
    )


@router.post(
    "/types",
    response_model=AllowanceTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create allowance type",
)
def create_allowance_type(payload: AllowanceTypeCreate, db: Session = Depends(get_db)):
    """Create a new allowance type for a company."""
    if payload.calculation_type not in VALID_CALCULATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"calculation_type must be one of {sorted(VALID_CALCULATION_TYPES)}",
            },
        )
    if payload.amount_basis not in VALID_AMOUNT_BASIS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"amount_basis must be one of {sorted(VALID_AMOUNT_BASIS)}",
            },
        )

    existing = (
        db.query(AllowanceType)
        .filter(
            AllowanceType.company_id == payload.company_id,
            AllowanceType.code == payload.code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate",
                "message": f"Allowance code '{payload.code}' already exists for this company",
            },
        )

    allowance = AllowanceType(**payload.model_dump())
    db.add(allowance)
    db.commit()
    db.refresh(allowance)
    return allowance


@router.patch(
    "/types/{allowance_type_id}",
    response_model=AllowanceTypeResponse,
    summary="Update allowance type",
)
def update_allowance_type(
    allowance_type_id: int,
    payload: AllowanceTypeUpdate,
    db: Session = Depends(get_db),
):
    """Partially update an allowance type."""
    allowance = (
        db.query(AllowanceType)
        .filter(AllowanceType.id == allowance_type_id)
        .first()
    )
    if not allowance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Allowance type {allowance_type_id} not found",
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

    if "amount_basis" in update_data:
        if update_data["amount_basis"] not in VALID_AMOUNT_BASIS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": f"amount_basis must be one of {sorted(VALID_AMOUNT_BASIS)}",
                },
            )

    if "code" in update_data:
        existing = (
            db.query(AllowanceType)
            .filter(
                AllowanceType.company_id == allowance.company_id,
                AllowanceType.code == update_data["code"],
                AllowanceType.id != allowance_type_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Duplicate",
                    "message": f"Allowance code '{update_data['code']}' already exists for this company",
                },
            )

    for field, value in update_data.items():
        setattr(allowance, field, value)

    db.commit()
    db.refresh(allowance)
    return allowance


@router.delete(
    "/types/{allowance_type_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete allowance type",
)
def delete_allowance_type(allowance_type_id: int, db: Session = Depends(get_db)):
    """Delete an allowance type. Fails if it is assigned to any employee."""
    allowance = (
        db.query(AllowanceType)
        .filter(AllowanceType.id == allowance_type_id)
        .first()
    )
    if not allowance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Allowance type {allowance_type_id} not found",
            },
        )

    count = (
        db.query(EmployeeAllowance)
        .filter(EmployeeAllowance.allowance_type_id == allowance_type_id)
        .count()
    )
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InUse",
                "message": f"Cannot delete: {count} employee allowance assignment(s) use this type.",
            },
        )

    db.delete(allowance)
    db.commit()
    return {"message": "Allowance type deleted"}


# ─── Allowance Matrix (Grade / Position / Department) ─────────────────────────


def _get_matrix_model(basis: str) -> Type:
    if basis not in VALID_MATRIX_BASIS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"basis must be one of {sorted(VALID_MATRIX_BASIS)}",
            },
        )
    return MATRIX_MODELS[basis]


def _get_entity_name(db: Session, basis: str, entity_id: int) -> str:
    model = ENTITY_MODELS[basis]
    field = ENTITY_NAME_FIELDS[basis]
    entity = db.query(model).filter(model.id == entity_id).first()
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidValue", "message": f"{basis} entity not found"},
        )
    return getattr(entity, field)


@router.get(
    "/types/{allowance_type_id}/matrix",
    response_model=List[AllowanceMatrixResponse],
    summary="List allowance matrix entries",
)
def list_allowance_matrix(
    allowance_type_id: int,
    basis: str = Query(..., description="Matrix basis: GRADE, POSITION, or DEPARTMENT"),
    db: Session = Depends(get_db),
):
    """List allowance matrix entries for a specific allowance type and basis."""
    model = _get_matrix_model(basis)
    allowance = db.query(AllowanceType).filter(AllowanceType.id == allowance_type_id).first()
    if not allowance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Allowance type not found"},
        )

    rows = (
        db.query(model)
        .filter(model.allowance_type_id == allowance_type_id)
        .order_by(model.effective_date.desc())
        .all()
    )

    return [
        {
            "id": row.id,
            "allowance_type_id": row.allowance_type_id,
            "entity_id": getattr(row, f"{basis.lower()}_id"),
            "entity_name": _get_entity_name(db, basis, getattr(row, f"{basis.lower()}_id")),
            "amount": row.amount,
            "effective_date": row.effective_date,
            "end_date": row.end_date,
            "is_active": row.is_active,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


@router.post(
    "/types/{allowance_type_id}/matrix",
    response_model=AllowanceMatrixResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create allowance matrix entry",
)
def create_allowance_matrix(
    allowance_type_id: int,
    basis: str = Query(..., description="Matrix basis: GRADE, POSITION, or DEPARTMENT"),
    payload: AllowanceMatrixCreate = None,
    db: Session = Depends(get_db),
):
    """Create an allowance matrix entry for grade/position/department."""
    model = _get_matrix_model(basis)
    allowance = db.query(AllowanceType).filter(AllowanceType.id == allowance_type_id).first()
    if not allowance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Allowance type not found"},
        )
    if allowance.amount_basis != basis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"Allowance type amount_basis is {allowance.amount_basis}, cannot create {basis} matrix",
            },
        )

    entity_id = payload.entity_id
    _get_entity_name(db, basis, entity_id)  # validate entity exists

    existing = (
        db.query(model)
        .filter(
            model.allowance_type_id == allowance_type_id,
            getattr(model, f"{basis.lower()}_id") == entity_id,
            model.effective_date == payload.effective_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Duplicate",
                "message": "Matrix entry already exists for this entity and effective date",
            },
        )

    row = model(
        allowance_type_id=allowance_type_id,
        **{f"{basis.lower()}_id": entity_id},
        amount=payload.amount,
        effective_date=payload.effective_date,
        end_date=payload.end_date,
        is_active=payload.is_active,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return {
        "id": row.id,
        "allowance_type_id": row.allowance_type_id,
        "entity_id": getattr(row, f"{basis.lower()}_id"),
        "entity_name": _get_entity_name(db, basis, getattr(row, f"{basis.lower()}_id")),
        "amount": row.amount,
        "effective_date": row.effective_date,
        "end_date": row.end_date,
        "is_active": row.is_active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


@router.patch(
    "/matrix/{matrix_id}",
    response_model=AllowanceMatrixResponse,
    summary="Update allowance matrix entry",
)
def update_allowance_matrix(
    matrix_id: int,
    basis: str = Query(..., description="Matrix basis: GRADE, POSITION, or DEPARTMENT"),
    payload: AllowanceMatrixUpdate = None,
    db: Session = Depends(get_db),
):
    """Partially update an allowance matrix entry."""
    model = _get_matrix_model(basis)
    row = db.query(model).filter(model.id == matrix_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Matrix entry not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "entity_id" in update_data:
        _get_entity_name(db, basis, update_data["entity_id"])

    if "entity_id" in update_data or "effective_date" in update_data:
        existing = (
            db.query(model)
            .filter(
                model.allowance_type_id == row.allowance_type_id,
                getattr(model, f"{basis.lower()}_id") == update_data.get(
                    "entity_id", getattr(row, f"{basis.lower()}_id")
                ),
                model.effective_date == update_data.get("effective_date", row.effective_date),
                model.id != matrix_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Duplicate",
                    "message": "Matrix entry already exists for this entity and effective date",
                },
            )

    for field, value in update_data.items():
        if field == "entity_id":
            setattr(row, f"{basis.lower()}_id", value)
        else:
            setattr(row, field, value)

    db.commit()
    db.refresh(row)

    return {
        "id": row.id,
        "allowance_type_id": row.allowance_type_id,
        "entity_id": getattr(row, f"{basis.lower()}_id"),
        "entity_name": _get_entity_name(db, basis, getattr(row, f"{basis.lower()}_id")),
        "amount": row.amount,
        "effective_date": row.effective_date,
        "end_date": row.end_date,
        "is_active": row.is_active,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


@router.delete(
    "/matrix/{matrix_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete allowance matrix entry",
)
def delete_allowance_matrix(
    matrix_id: int,
    basis: str = Query(..., description="Matrix basis: GRADE, POSITION, or DEPARTMENT"),
    db: Session = Depends(get_db),
):
    """Delete an allowance matrix entry."""
    model = _get_matrix_model(basis)
    row = db.query(model).filter(model.id == matrix_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Matrix entry not found"},
        )

    db.delete(row)
    db.commit()
    return {"message": "Matrix entry deleted"}
