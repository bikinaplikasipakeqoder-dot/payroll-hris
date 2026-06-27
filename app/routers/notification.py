"""Notification endpoints for in-app notification system."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.integration import Notification
from app.schemas.payslip_pdf import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    employee_id: int = Query(None),
    user_id: int = Query(None),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """List notifications, optionally filtered by employee/user and read status."""
    query = db.query(Notification)

    if employee_id is not None:
        query = query.filter(Notification.employee_id == employee_id)
    if user_id is not None:
        query = query.filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = (
        query.order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )

    return [
        NotificationResponse(
            id=n.id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            link=n.link,
            is_read=n.is_read,
            created_at=n.created_at.isoformat() if n.created_at else "",
        )
        for n in notifications
    ]


@router.get("/unread-count")
def get_unread_count(
    employee_id: int = Query(None),
    user_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Get count of unread notifications."""
    query = db.query(Notification).filter(Notification.is_read == False)

    if employee_id is not None:
        query = query.filter(Notification.employee_id == employee_id)
    if user_id is not None:
        query = query.filter(Notification.user_id == user_id)

    count = query.count()
    return {"count": count}


@router.patch("/{notification_id}/read")
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark a notification as read."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.now()
    db.commit()

    return {"success": True}
