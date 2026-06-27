"""
BPJS configuration API endpoints.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bpjs import BpjsSetting
from app.schemas.bpjs import BpjsSettingCreate, BpjsSettingResponse, BpjsSettingUpdate

router = APIRouter(prefix="/bpjs", tags=["BPJS Configuration"])

VALID_BPJS_TYPES = {"KESEHATAN", "JHT", "JP", "JKK", "JKM"}


def _has_overlap(
    db: Session,
    company_id: int,
    bpjs_type: str,
    effective_date: date,
    end_date: Optional[date],
    exclude_id: Optional[int] = None,
) -> bool:
    """Return True if an active setting overlaps with the given date range."""
    query = db.query(BpjsSetting).filter(
        BpjsSetting.company_id == company_id,
        BpjsSetting.bpjs_type == bpjs_type,
        BpjsSetting.is_active == True,
    )
    if exclude_id is not None:
        query = query.filter(BpjsSetting.id != exclude_id)

    existing = query.all()
    for row in existing:
        row_end = row.end_date or date.max
        new_end = end_date or date.max
        # Overlap if existing.start <= new_end and new_start <= existing_end
        if row.effective_date <= new_end and effective_date <= row_end:
            return True
    return False



@router.get(
    "/settings",
    response_model=List[BpjsSettingResponse],
    summary="List BPJS settings",
)
def list_bpjs_settings(
    company_id: int = Query(..., description="Company ID"),
    db: Session = Depends(get_db),
):
    """List all BPJS contribution settings for the specified company."""
    settings = (
        db.query(BpjsSetting)
        .filter(BpjsSetting.company_id == company_id, BpjsSetting.is_active == True)
        .order_by(BpjsSetting.bpjs_type)
        .all()
    )
    return settings


@router.post(
    "/settings",
    response_model=BpjsSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create BPJS setting",
)
def create_bpjs_setting(payload: BpjsSettingCreate, db: Session = Depends(get_db)):
    """Create a new BPJS contribution setting."""
    if payload.bpjs_type not in VALID_BPJS_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidValue",
                "message": f"bpjs_type must be one of {sorted(VALID_BPJS_TYPES)}",
            },
        )

    if _has_overlap(
        db,
        payload.company_id,
        payload.bpjs_type,
        payload.effective_date,
        payload.end_date,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Overlap",
                "message": "An active BPJS setting already exists for this type within the given date range",
            },
        )

    setting = BpjsSetting(**payload.model_dump())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


@router.patch(
    "/settings/{setting_id}",
    response_model=BpjsSettingResponse,
    summary="Update BPJS rates/caps",
)
def update_bpjs_setting(
    setting_id: int,
    payload: BpjsSettingUpdate,
    db: Session = Depends(get_db),
):
    """Update BPJS contribution rates or salary caps for a specific setting."""
    setting = db.query(BpjsSetting).filter(BpjsSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"BPJS setting {setting_id} not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)

    effective_date = update_data.get("effective_date", setting.effective_date)
    end_date = update_data.get("end_date", setting.end_date)

    if "effective_date" in update_data or "end_date" in update_data:
        if _has_overlap(
            db,
            setting.company_id,
            setting.bpjs_type,
            effective_date,
            end_date,
            exclude_id=setting_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Overlap",
                    "message": "An active BPJS setting already exists for this type within the given date range",
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
    summary="Delete BPJS setting",
)
def delete_bpjs_setting(setting_id: int, db: Session = Depends(get_db)):
    """Delete a BPJS setting."""
    setting = db.query(BpjsSetting).filter(BpjsSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": f"BPJS setting {setting_id} not found"},
        )

    db.delete(setting)
    db.commit()
    return {"message": "BPJS setting deleted"}
