"""
Tax configuration API endpoints.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.tax import PtkpValue, TaxBracketPasal17, TaxSetting, TerBracket
from app.schemas.tax import (
    PtkpValueCreate,
    PtkpValueResponse,
    PtkpValueUpdate,
    TaxBracketCreate,
    TaxBracketResponse,
    TaxBracketUpdate,
    TaxSettingCreate,
    TaxSettingResponse,
    TaxSettingUpdate,
    TerBracketCreate,
    TerBracketResponse,
    TerBracketUpdate,
)

router = APIRouter(prefix="/tax", tags=["Tax Configuration"])

VALID_TAX_METHODS = {"PASAL_17", "TER"}
VALID_PAYROLL_METHODS = {"GROSS", "GROSS_UP", "NETT"}
VALID_TER_CATEGORIES = {"A", "B", "C"}


def _ranges_overlap(
    a_min: Decimal,
    a_max: Optional[Decimal],
    b_min: Decimal,
    b_max: Optional[Decimal],
) -> bool:
    """Return True if two numeric intervals overlap."""
    a_end = a_max if a_max is not None else Decimal("Infinity")
    b_end = b_max if b_max is not None else Decimal("Infinity")
    return a_min <= b_end and b_min <= a_end


def _date_ranges_overlap(
    a_start: date,
    a_end: Optional[date],
    b_start: date,
    b_end: Optional[date],
) -> bool:
    """Return True if two date intervals overlap."""
    a_e = a_end or date.max
    b_e = b_end or date.max
    return a_start <= b_e and b_start <= a_e


# ─── Tax Settings ─────────────────────────────────────────────────────────────


@router.get(
    "/settings",
    response_model=List[TaxSettingResponse],
    summary="Get tax settings for a company",
)
def get_tax_settings(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """Retrieve tax calculation settings for the specified company."""
    settings = (
        db.query(TaxSetting)
        .filter(TaxSetting.company_id == company_id)
        .all()
    )
    return settings


@router.post(
    "/settings",
    response_model=TaxSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tax setting",
)
def create_tax_setting(payload: TaxSettingCreate, db: Session = Depends(get_db)):
    """Create tax calculation settings for a company."""
    if payload.tax_calculation_method not in VALID_TAX_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"tax_calculation_method must be one of {sorted(VALID_TAX_METHODS)}",
            },
        )
    if payload.payroll_method not in VALID_PAYROLL_METHODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"payroll_method must be one of {sorted(VALID_PAYROLL_METHODS)}",
            },
        )

    existing = (
        db.query(TaxSetting)
        .filter(TaxSetting.company_id == payload.company_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate",
                "message": "Tax setting already exists for this company",
            },
        )

    setting = TaxSetting(**payload.model_dump())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


@router.patch(
    "/settings/{setting_id}",
    response_model=TaxSettingResponse,
    summary="Update tax setting",
)
def update_tax_setting(
    setting_id: int,
    payload: TaxSettingUpdate,
    db: Session = Depends(get_db),
):
    """Update tax calculation method for a company."""
    setting = db.query(TaxSetting).filter(TaxSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Tax setting {setting_id} not found",
            },
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "tax_calculation_method" in update_data:
        if update_data["tax_calculation_method"] not in VALID_TAX_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": f"tax_calculation_method must be one of {sorted(VALID_TAX_METHODS)}",
                },
            )

    if "payroll_method" in update_data:
        if update_data["payroll_method"] not in VALID_PAYROLL_METHODS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "InvalidValue",
                    "message": f"payroll_method must be one of {sorted(VALID_PAYROLL_METHODS)}",
                },
            )

    for field, value in update_data.items():
        setattr(setting, field, value)

    db.commit()
    db.refresh(setting)
    return setting


@router.delete(
    "/settings/{setting_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete tax setting",
)
def delete_tax_setting(setting_id: int, db: Session = Depends(get_db)):
    """Delete a tax setting."""
    setting = db.query(TaxSetting).filter(TaxSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Tax setting {setting_id} not found",
            },
        )

    db.delete(setting)
    db.commit()
    return {"message": "Tax setting deleted"}


# ─── PTKP Values ──────────────────────────────────────────────────────────────


@router.get(
    "/ptkp",
    response_model=List[PtkpValueResponse],
    summary="List PTKP values",
)
def list_ptkp_values(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all PTKP (non-taxable income) threshold values for the company."""
    values = (
        db.query(PtkpValue)
        .filter(PtkpValue.company_id == company_id, PtkpValue.is_active == True)
        .order_by(PtkpValue.ptkp_code)
        .all()
    )
    return values


@router.post(
    "/ptkp",
    response_model=PtkpValueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create PTKP value",
)
def create_ptkp_value(payload: PtkpValueCreate, db: Session = Depends(get_db)):
    """Create a new PTKP threshold value."""
    existing = (
        db.query(PtkpValue)
        .filter(
            PtkpValue.company_id == payload.company_id,
            PtkpValue.ptkp_code == payload.ptkp_code,
            PtkpValue.effective_date == payload.effective_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate",
                "message": "PTKP value already exists for this code and effective date",
            },
        )

    value = PtkpValue(**payload.model_dump())
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@router.patch(
    "/ptkp/{ptkp_id}",
    response_model=PtkpValueResponse,
    summary="Update PTKP value",
)
def update_ptkp_value(
    ptkp_id: int,
    payload: PtkpValueUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a PTKP value."""
    value = db.query(PtkpValue).filter(PtkpValue.id == ptkp_id).first()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"PTKP value {ptkp_id} not found",
            },
        )

    update_data = payload.model_dump(exclude_unset=True)

    if "ptkp_code" in update_data or "effective_date" in update_data:
        existing = (
            db.query(PtkpValue)
            .filter(
                PtkpValue.company_id == value.company_id,
                PtkpValue.ptkp_code == update_data.get("ptkp_code", value.ptkp_code),
                PtkpValue.effective_date == update_data.get("effective_date", value.effective_date),
                PtkpValue.id != ptkp_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Duplicate",
                    "message": "PTKP value already exists for this code and effective date",
                },
            )

    for field, val in update_data.items():
        setattr(value, field, val)

    db.commit()
    db.refresh(value)
    return value


@router.delete(
    "/ptkp/{ptkp_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete PTKP value",
)
def delete_ptkp_value(ptkp_id: int, db: Session = Depends(get_db)):
    """Delete a PTKP value."""
    value = db.query(PtkpValue).filter(PtkpValue.id == ptkp_id).first()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"PTKP value {ptkp_id} not found",
            },
        )

    db.delete(value)
    db.commit()
    return {"message": "PTKP value deleted"}


# ─── Pasal 17 Tax Brackets ────────────────────────────────────────────────────


@router.get(
    "/brackets",
    response_model=List[TaxBracketResponse],
    summary="List Pasal 17 progressive tax brackets",
)
def list_tax_brackets(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List PPh Pasal 17 progressive tax brackets for the company."""
    brackets = (
        db.query(TaxBracketPasal17)
        .filter(
            TaxBracketPasal17.company_id == company_id,
            TaxBracketPasal17.is_active == True,
        )
        .order_by(TaxBracketPasal17.bracket_order)
        .all()
    )
    return brackets


def _validate_tax_bracket(
    db: Session,
    company_id: int,
    bracket_order: int,
    income_min: Decimal,
    income_max: Optional[Decimal],
    effective_date: date,
    end_date: Optional[date],
    exclude_id: Optional[int] = None,
):
    """Validate a Pasal 17 bracket against duplicates and overlapping ranges."""
    query = db.query(TaxBracketPasal17).filter(
        TaxBracketPasal17.company_id == company_id,
        TaxBracketPasal17.bracket_order == bracket_order,
        TaxBracketPasal17.is_active == True,
    )
    if exclude_id is not None:
        query = query.filter(TaxBracketPasal17.id != exclude_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Duplicate",
                "message": f"Bracket order {bracket_order} already exists for this company",
            },
        )

    query = db.query(TaxBracketPasal17).filter(
        TaxBracketPasal17.company_id == company_id,
        TaxBracketPasal17.is_active == True,
    )
    if exclude_id is not None:
        query = query.filter(TaxBracketPasal17.id != exclude_id)

    for row in query.all():
        if _date_ranges_overlap(
            row.effective_date,
            row.end_date,
            effective_date,
            end_date,
        ) and _ranges_overlap(
            row.income_range_min,
            row.income_range_max,
            income_min,
            income_max,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Overlap",
                    "message": "This bracket overlaps with an existing active bracket",
                },
            )


@router.post(
    "/brackets",
    response_model=TaxBracketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Pasal 17 tax bracket",
)
def create_tax_bracket(payload: TaxBracketCreate, db: Session = Depends(get_db)):
    """Create a new PPh Pasal 17 progressive tax bracket."""
    _validate_tax_bracket(
        db,
        payload.company_id,
        payload.bracket_order,
        payload.income_range_min,
        payload.income_range_max,
        payload.effective_date,
        payload.end_date,
    )

    bracket = TaxBracketPasal17(**payload.model_dump())
    db.add(bracket)
    db.commit()
    db.refresh(bracket)
    return bracket


@router.patch(
    "/brackets/{bracket_id}",
    response_model=TaxBracketResponse,
    summary="Update Pasal 17 tax bracket",
)
def update_tax_bracket(
    bracket_id: int,
    payload: TaxBracketUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a PPh Pasal 17 tax bracket."""
    bracket = db.query(TaxBracketPasal17).filter(TaxBracketPasal17.id == bracket_id).first()
    if not bracket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Tax bracket {bracket_id} not found",
            },
        )

    update_data = payload.model_dump(exclude_unset=True)

    if any(k in update_data for k in ("bracket_order", "income_range_min", "income_range_max", "effective_date", "end_date")):
        _validate_tax_bracket(
            db,
            bracket.company_id,
            update_data.get("bracket_order", bracket.bracket_order),
            update_data.get("income_range_min", bracket.income_range_min),
            update_data.get("income_range_max", bracket.income_range_max),
            update_data.get("effective_date", bracket.effective_date),
            update_data.get("end_date", bracket.end_date),
            exclude_id=bracket_id,
        )

    for field, val in update_data.items():
        setattr(bracket, field, val)

    db.commit()
    db.refresh(bracket)
    return bracket


@router.delete(
    "/brackets/{bracket_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Pasal 17 tax bracket",
)
def delete_tax_bracket(bracket_id: int, db: Session = Depends(get_db)):
    """Delete a PPh Pasal 17 tax bracket."""
    bracket = db.query(TaxBracketPasal17).filter(TaxBracketPasal17.id == bracket_id).first()
    if not bracket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"Tax bracket {bracket_id} not found",
            },
        )

    db.delete(bracket)
    db.commit()
    return {"message": "Tax bracket deleted"}


# ─── TER Brackets ─────────────────────────────────────────────────────────────


@router.get(
    "/ter-brackets",
    response_model=List[TerBracketResponse],
    summary="List TER brackets",
)
def list_ter_brackets(
    company_id: int = Query(..., description="Company ID"),
    category: Optional[str] = Query(None, description="Filter by category (A, B, C)"),
    db: Session = Depends(get_db),
):
    """List TER (Tarif Efektif Rata-rata) brackets for the company."""
    query = db.query(TerBracket).filter(
        TerBracket.company_id == company_id,
        TerBracket.is_active == True,
    )

    if category is not None:
        query = query.filter(TerBracket.category == category)

    brackets = query.order_by(TerBracket.category, TerBracket.income_range_min).all()
    return brackets


def _validate_ter_bracket(
    db: Session,
    company_id: int,
    category: str,
    income_min: Decimal,
    income_max: Optional[Decimal],
    effective_date: date,
    end_date: Optional[date],
    exclude_id: Optional[int] = None,
):
    """Validate a TER bracket category and overlapping ranges."""
    if category not in VALID_TER_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"category must be one of {sorted(VALID_TER_CATEGORIES)}",
            },
        )

    query = db.query(TerBracket).filter(
        TerBracket.company_id == company_id,
        TerBracket.category == category,
        TerBracket.is_active == True,
    )
    if exclude_id is not None:
        query = query.filter(TerBracket.id != exclude_id)

    for row in query.all():
        if _date_ranges_overlap(
            row.effective_date,
            row.end_date,
            effective_date,
            end_date,
        ) and _ranges_overlap(
            row.income_range_min,
            row.income_range_max,
            income_min,
            income_max,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Overlap",
                    "message": "This TER bracket overlaps with an existing active bracket",
                },
            )


@router.post(
    "/ter-brackets",
    response_model=TerBracketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create TER bracket",
)
def create_ter_bracket(payload: TerBracketCreate, db: Session = Depends(get_db)):
    """Create a new TER bracket."""
    _validate_ter_bracket(
        db,
        payload.company_id,
        payload.category,
        payload.income_range_min,
        payload.income_range_max,
        payload.effective_date,
        payload.end_date,
    )

    bracket = TerBracket(**payload.model_dump())
    db.add(bracket)
    db.commit()
    db.refresh(bracket)
    return bracket


@router.patch(
    "/ter-brackets/{bracket_id}",
    response_model=TerBracketResponse,
    summary="Update TER bracket",
)
def update_ter_bracket(
    bracket_id: int,
    payload: TerBracketUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a TER bracket."""
    bracket = db.query(TerBracket).filter(TerBracket.id == bracket_id).first()
    if not bracket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"TER bracket {bracket_id} not found",
            },
        )

    update_data = payload.model_dump(exclude_unset=True)

    if any(k in update_data for k in ("category", "income_range_min", "income_range_max", "effective_date", "end_date")):
        _validate_ter_bracket(
            db,
            bracket.company_id,
            update_data.get("category", bracket.category),
            update_data.get("income_range_min", bracket.income_range_min),
            update_data.get("income_range_max", bracket.income_range_max),
            update_data.get("effective_date", bracket.effective_date),
            update_data.get("end_date", bracket.end_date),
            exclude_id=bracket_id,
        )

    for field, val in update_data.items():
        setattr(bracket, field, val)

    db.commit()
    db.refresh(bracket)
    return bracket


@router.delete(
    "/ter-brackets/{bracket_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete TER bracket",
)
def delete_ter_bracket(bracket_id: int, db: Session = Depends(get_db)):
    """Delete a TER bracket."""
    bracket = db.query(TerBracket).filter(TerBracket.id == bracket_id).first()
    if not bracket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "message": f"TER bracket {bracket_id} not found",
            },
        )

    db.delete(bracket)
    db.commit()
    return {"message": "TER bracket deleted"}
