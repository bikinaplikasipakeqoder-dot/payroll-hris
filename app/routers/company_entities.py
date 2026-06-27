"""
Company Entity and UMP settings API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company_entity import Entity, UmpSetting
from app.schemas.company_entity import (
    EntityCreate, EntityResponse, EntityUpdate,
    UmpSettingCreate, UmpSettingResponse, UmpSettingUpdate,
)

router = APIRouter(prefix="/companies", tags=["Companies & Entities"])


def _validate_entity_province(db: Session, company_id: int, province: Optional[str]) -> None:
    """Ensure the entity province exists in UMP settings."""
    if not province:
        return

    ump_exists = (
        db.query(UmpSetting)
        .filter(
            UmpSetting.company_id == company_id,
            UmpSetting.province.ilike(province.strip()),
            UmpSetting.is_active == True,
        )
        .first()
    )
    if not ump_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "UmpProvinceNotFound",
                "message": f"Provinsi '{province}' belum terdaftar di master UMP. Tambahkan UMP untuk provinsi tersebut terlebih dahulu.",
            },
        )


# ─── Entities ───────────────────────────────────────────────────────────────


@router.get(
    "/{company_id}/entities",
    response_model=List[EntityResponse],
    summary="List company entities",
)
def list_entities(
    company_id: int,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """List all entities/branches for a company."""
    query = db.query(Entity).filter(Entity.company_id == company_id)
    if is_active is not None:
        query = query.filter(Entity.is_active == is_active)
    return query.order_by(Entity.code).all()


@router.post(
    "/{company_id}/entities",
    response_model=EntityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a company entity",
)
def create_entity(company_id: int, payload: EntityCreate, db: Session = Depends(get_db)):
    """Create a new entity/branch for a company."""
    existing = (
        db.query(Entity)
        .filter(Entity.company_id == company_id, Entity.code == payload.code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DuplicateEntity",
                "message": f"Entity code '{payload.code}' already exists for this company",
            },
        )

    _validate_entity_province(db, company_id, payload.province)

    entity = Entity(company_id=company_id, **payload.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.get(
    "/{company_id}/entities/{entity_id}",
    response_model=EntityResponse,
    summary="Get entity detail",
)
def get_entity(company_id: int, entity_id: int, db: Session = Depends(get_db)):
    """Retrieve a single entity by ID."""
    entity = (
        db.query(Entity)
        .filter(Entity.company_id == company_id, Entity.id == entity_id)
        .first()
    )
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Entity not found"},
        )
    return entity


@router.patch(
    "/{company_id}/entities/{entity_id}",
    response_model=EntityResponse,
    summary="Update entity (partial)",
)
def update_entity(
    company_id: int,
    entity_id: int,
    payload: EntityUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a company entity."""
    entity = (
        db.query(Entity)
        .filter(Entity.company_id == company_id, Entity.id == entity_id)
        .first()
    )
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Entity not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)

    _validate_entity_province(db, company_id, entity.province)

    db.commit()
    db.refresh(entity)
    return entity


@router.delete(
    "/{company_id}/entities/{entity_id}",
    response_model=EntityResponse,
    summary="Deactivate entity (soft delete)",
)
def deactivate_entity(company_id: int, entity_id: int, db: Session = Depends(get_db)):
    """Soft-delete an entity by setting is_active=False."""
    entity = (
        db.query(Entity)
        .filter(Entity.company_id == company_id, Entity.id == entity_id)
        .first()
    )
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Entity not found"},
        )

    entity.is_active = False
    db.commit()
    db.refresh(entity)
    return entity


# ─── UMP Settings ─────────────────────────────────────────────────────────────


@router.get(
    "/{company_id}/ump-settings",
    response_model=List[UmpSettingResponse],
    summary="List UMP settings",
)
def list_ump_settings(
    company_id: int,
    province: Optional[str] = Query(None, description="Filter by province"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """List UMP settings for a company."""
    query = db.query(UmpSetting).filter(UmpSetting.company_id == company_id)
    if province:
        query = query.filter(UmpSetting.province.ilike(f"%{province}%"))
    if is_active is not None:
        query = query.filter(UmpSetting.is_active == is_active)
    return query.order_by(UmpSetting.province, UmpSetting.city).all()


@router.post(
    "/{company_id}/ump-settings",
    response_model=UmpSettingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a UMP setting",
)
def create_ump_setting(
    company_id: int, payload: UmpSettingCreate, db: Session = Depends(get_db)
):
    """Create a new UMP setting for a province/city."""
    existing = (
        db.query(UmpSetting)
        .filter(
            UmpSetting.company_id == company_id,
            UmpSetting.province == payload.province,
            UmpSetting.city == payload.city,
            UmpSetting.effective_date == payload.effective_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DuplicateUmpSetting",
                "message": "UMP setting already exists for this location and effective date",
            },
        )

    setting = UmpSetting(company_id=company_id, **payload.model_dump())
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


@router.get(
    "/{company_id}/ump-settings/{ump_id}",
    response_model=UmpSettingResponse,
    summary="Get UMP setting detail",
)
def get_ump_setting(company_id: int, ump_id: int, db: Session = Depends(get_db)):
    """Retrieve a single UMP setting."""
    setting = (
        db.query(UmpSetting)
        .filter(UmpSetting.company_id == company_id, UmpSetting.id == ump_id)
        .first()
    )
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "UMP setting not found"},
        )
    return setting


@router.patch(
    "/{company_id}/ump-settings/{ump_id}",
    response_model=UmpSettingResponse,
    summary="Update UMP setting (partial)",
)
def update_ump_setting(
    company_id: int,
    ump_id: int,
    payload: UmpSettingUpdate,
    db: Session = Depends(get_db),
):
    """Partially update a UMP setting."""
    setting = (
        db.query(UmpSetting)
        .filter(UmpSetting.company_id == company_id, UmpSetting.id == ump_id)
        .first()
    )
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "UMP setting not found"},
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)

    db.commit()
    db.refresh(setting)
    return setting


@router.delete(
    "/{company_id}/ump-settings/{ump_id}",
    response_model=UmpSettingResponse,
    summary="Deactivate UMP setting (soft delete)",
)
def deactivate_ump_setting(company_id: int, ump_id: int, db: Session = Depends(get_db)):
    """Soft-delete a UMP setting by setting is_active=False."""
    setting = (
        db.query(UmpSetting)
        .filter(UmpSetting.company_id == company_id, UmpSetting.id == ump_id)
        .first()
    )
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "UMP setting not found"},
        )

    setting.is_active = False
    db.commit()
    db.refresh(setting)
    return setting
