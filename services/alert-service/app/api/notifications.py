"""API routes for unified notifications."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.database.session import SessionLocal
from app.services.notification_service import NotificationService


router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"],
)


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
async def get_notifications(
    db: Session = Depends(get_db),
):
    """Get all unified price, prediction, and macro notifications."""
    service = NotificationService(db)

    total, notifications = service.get_all_notifications()

    return {
        "total": total,
        "notifications": [
            notification.to_dict()
            for notification in notifications
        ],
    }


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    service = NotificationService(db)

    notification = service.mark_as_read(notification_id)

    if notification is None:
        return {
            "success": False,
            "message": "Notification not found",
        }

    return {
        "success": True,
        "notification": notification.to_dict(),
    }


@router.post("/read-all")
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    service = NotificationService(db)

    count = service.mark_all_notifications_as_read()

    return {
        "count": count,
    }