"""
Rules Engine admin API endpoints.
"""

import json
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.rules import RuleCategory, RuleConfiguration, RuleAuditLog, RuleVariable
from app.schemas.rules import (
    RuleCategoryResponse,
    RuleConfigurationCreate,
    RuleConfigurationUpdate,
    RuleConfigurationResponse,
    RuleVariableResponse,
    RuleAuditLogResponse,
    RuleResetRequest,
)

router = APIRouter(prefix="/admin/rules", tags=["Rules Engine"])


def _rule_to_dict(rule: RuleConfiguration) -> dict:
    """Serialize a rule configuration to a plain dict for audit logging."""
    return {
        "id": rule.id,
        "company_id": rule.company_id,
        "category_id": rule.category_id,
        "rule_code": rule.rule_code,
        "rule_name": rule.rule_name,
        "rule_type": rule.rule_type,
        "formula": rule.formula,
        "value": str(rule.value) if rule.value is not None else None,
        "min_value": str(rule.min_value) if rule.min_value is not None else None,
        "max_value": str(rule.max_value) if rule.max_value is not None else None,
        "rate": str(rule.rate) if rule.rate is not None else None,
        "effective_date": rule.effective_date.isoformat() if rule.effective_date else None,
        "expiry_date": rule.expiry_date.isoformat() if rule.expiry_date else None,
        "priority": rule.priority,
        "is_active": rule.is_active,
        "description": rule.description,
    }


def _log_rule_change(
    db: Session,
    rule: RuleConfiguration,
    action: str,
    changed_by: int,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    reason: Optional[str] = None,
) -> None:
    """Insert an audit log entry for a rule change."""
    audit = RuleAuditLog(
        rule_id=rule.id,
        action=action,
        old_value=json.dumps(old_value) if old_value is not None else None,
        new_value=json.dumps(new_value) if new_value is not None else None,
        changed_by=changed_by,
        reason=reason,
    )
    db.add(audit)


def _build_rule_response(rule: RuleConfiguration) -> dict:
    """Build a response dict including category info and creator names."""
    return {
        **_rule_to_dict(rule),
        "category_code": rule.category.category_code if rule.category else None,
        "category_name": rule.category.category_name if rule.category else None,
        "created_by_name": rule.creator.full_name if rule.creator else None,
        "updated_by_name": rule.updater.full_name if rule.updater else None,
    }


@router.get(
    "/categories",
    response_model=List[RuleCategoryResponse],
    summary="List rule categories",
)
def list_rule_categories(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """List all rule categories."""
    query = db.query(RuleCategory)
    if is_active is not None:
        query = query.filter(RuleCategory.is_active == is_active)
    return query.order_by(RuleCategory.category_code).all()


@router.get(
    "/configurations",
    response_model=List[RuleConfigurationResponse],
    summary="List rule configurations",
)
def list_rule_configurations(
    company_id: int = Query(..., description="Company ID"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    rule_code: Optional[str] = Query(None, description="Filter by rule code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    effective_date: Optional[date] = Query(None, description="Filter by effective date"),
    db: Session = Depends(get_db),
):
    """List rule configurations with optional filters."""
    query = db.query(RuleConfiguration).filter(RuleConfiguration.company_id == company_id)

    if category_id is not None:
        query = query.filter(RuleConfiguration.category_id == category_id)
    if rule_code:
        query = query.filter(RuleConfiguration.rule_code.ilike(f"%{rule_code}%"))
    if is_active is not None:
        query = query.filter(RuleConfiguration.is_active == is_active)
    if effective_date is not None:
        query = query.filter(RuleConfiguration.effective_date <= effective_date)
        query = query.filter(
            (RuleConfiguration.expiry_date.is_(None))
            | (RuleConfiguration.expiry_date >= effective_date)
        )

    rules = query.order_by(RuleConfiguration.rule_code, RuleConfiguration.effective_date.desc()).all()
    return [_build_rule_response(rule) for rule in rules]


@router.post(
    "/configurations",
    response_model=RuleConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a rule configuration",
)
def create_rule_configuration(
    payload: RuleConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new rule configuration and log the change."""
    category = db.query(RuleCategory).filter(RuleCategory.id == payload.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidCategory", "message": "Rule category not found"},
        )

    existing = (
        db.query(RuleConfiguration)
        .filter(
            RuleConfiguration.company_id == payload.company_id,
            RuleConfiguration.rule_code == payload.rule_code,
            RuleConfiguration.effective_date == payload.effective_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "DuplicateRule",
                "message": f"Rule '{payload.rule_code}' already exists for this effective date",
            },
        )

    rule = RuleConfiguration(
        company_id=payload.company_id,
        category_id=payload.category_id,
        rule_code=payload.rule_code,
        rule_name=payload.rule_name,
        rule_type=payload.rule_type,
        formula=payload.formula,
        value=payload.value,
        min_value=payload.min_value,
        max_value=payload.max_value,
        rate=payload.rate,
        effective_date=payload.effective_date,
        expiry_date=payload.expiry_date,
        priority=payload.priority,
        is_active=payload.is_active,
        description=payload.description,
        created_by=current_user.get("user_id"),
        updated_by=current_user.get("user_id"),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    _log_rule_change(
        db, rule, "CREATE", current_user.get("user_id"), new_value=_rule_to_dict(rule)
    )
    db.commit()
    db.refresh(rule)

    return _build_rule_response(rule)


@router.get(
    "/configurations/{rule_id}",
    response_model=RuleConfigurationResponse,
    summary="Get rule configuration detail",
)
def get_rule_configuration(rule_id: int, db: Session = Depends(get_db)):
    """Retrieve a single rule configuration by ID."""
    rule = db.query(RuleConfiguration).filter(RuleConfiguration.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Rule configuration not found"},
        )
    return _build_rule_response(rule)


@router.patch(
    "/configurations/{rule_id}",
    response_model=RuleConfigurationResponse,
    summary="Update rule configuration",
)
def update_rule_configuration(
    rule_id: int,
    payload: RuleConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Partially update a rule configuration and log the change."""
    rule = db.query(RuleConfiguration).filter(RuleConfiguration.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Rule configuration not found"},
        )

    old_value = _rule_to_dict(rule)
    update_data = payload.model_dump(exclude_unset=True)

    if "category_id" in update_data:
        category = db.query(RuleCategory).filter(
            RuleCategory.id == update_data["category_id"]
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "InvalidCategory", "message": "Rule category not found"},
            )

    for field, value in update_data.items():
        setattr(rule, field, value)

    rule.updated_by = current_user.get("user_id")

    db.commit()
    db.refresh(rule)

    action = "UPDATE"
    if "is_active" in update_data:
        action = "ACTIVATE" if rule.is_active else "DEACTIVATE"

    _log_rule_change(
        db,
        rule,
        action,
        current_user.get("user_id"),
        old_value=old_value,
        new_value=_rule_to_dict(rule),
    )
    db.commit()
    db.refresh(rule)

    return _build_rule_response(rule)


@router.delete(
    "/configurations/{rule_id}",
    summary="Delete rule configuration",
)
def delete_rule_configuration(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a rule configuration and log the change."""
    rule = db.query(RuleConfiguration).filter(RuleConfiguration.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Rule configuration not found"},
        )

    old_value = _rule_to_dict(rule)

    _log_rule_change(
        db,
        rule,
        "DELETE",
        current_user.get("user_id"),
        old_value=old_value,
    )

    db.delete(rule)
    db.commit()

    return {"message": "Rule configuration deleted"}


@router.get(
    "/configurations/{rule_id}/audit-logs",
    response_model=List[RuleAuditLogResponse],
    summary="List audit logs for a rule",
)
def list_rule_audit_logs(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """List audit log entries for a rule configuration."""
    rule = db.query(RuleConfiguration).filter(RuleConfiguration.id == rule_id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NotFound", "message": "Rule configuration not found"},
        )

    logs = (
        db.query(RuleAuditLog)
        .filter(RuleAuditLog.rule_id == rule_id)
        .order_by(RuleAuditLog.changed_at.desc())
        .all()
    )

    return [
        {
            **log.__dict__,
            "changed_by_name": log.changer.full_name if log.changer else None,
        }
        for log in logs
    ]


@router.post(
    "/reset-to-default",
    summary="Reset rules in a category",
)
def reset_rules_to_default(
    payload: RuleResetRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Deactivate all active custom rules in a category for a company."""
    category = db.query(RuleCategory).filter(RuleCategory.id == payload.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "InvalidCategory", "message": "Rule category not found"},
        )

    rules = (
        db.query(RuleConfiguration)
        .filter(
            RuleConfiguration.company_id == payload.company_id,
            RuleConfiguration.category_id == payload.category_id,
            RuleConfiguration.is_active == True,
        )
        .all()
    )

    for rule in rules:
        old_value = _rule_to_dict(rule)
        rule.is_active = False
        rule.updated_by = current_user.get("user_id")
        _log_rule_change(
            db,
            rule,
            "DEACTIVATE",
            current_user.get("user_id"),
            old_value=old_value,
            new_value=_rule_to_dict(rule),
            reason=payload.reason or "Reset to default",
        )

    db.commit()

    return {
        "message": f"Deactivated {len(rules)} custom rules in category '{category.category_code}'",
        "deactivated_count": len(rules),
    }


@router.get(
    "/variables",
    response_model=List[RuleVariableResponse],
    summary="List rule variables",
)
def list_rule_variables(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
):
    """List all whitelisted variables available to formulas."""
    query = db.query(RuleVariable)
    if is_active is not None:
        query = query.filter(RuleVariable.is_active == is_active)
    return query.order_by(RuleVariable.variable_code).all()
