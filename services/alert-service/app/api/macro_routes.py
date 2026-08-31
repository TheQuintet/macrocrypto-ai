"""API routes for macro event alerts"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.database.session import SessionLocal
from app.models.macro_alert import (
    MacroEventAlert,
    MacroEventSubscription,
    MacroEventCache,
    MacroEventNotification,
    EventType,
    EventTiming,
    EventImpact,
    MacroAlertStatus
)
from app.schemas.macro_alert import (
    MacroSubscriptionCreate,
    MacroSubscriptionUpdate,
    MacroAlertCreate,
    MacroAlertUpdate,
    MacroAlertResponse,
    MacroEventResponse
)
from app.services.macro_alert_engine import MacroAlertEngine
from app.services.macro_notification_service import MacroNotificationService
from app.config import settings


router = APIRouter(
    prefix="/api/v1/macro",
    tags=["macro-alerts"]
)


def get_db():
    """Dependency for database session."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================
# SUBSCRIPTION MANAGEMENT
# ============================================

@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe_to_event(
    subscription_data: MacroSubscriptionCreate,
    db: Session = Depends(get_db)
):
    """Subscribe to a macro event type."""
    existing = db.query(MacroEventSubscription).filter(
        MacroEventSubscription.user_id == subscription_data.user_id,
        MacroEventSubscription.event_type == subscription_data.event_type
    ).first()

    if existing:
        existing.subscribed = subscription_data.subscribed
        existing.impact_filter = subscription_data.impact_filter
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing.to_dict()

    subscription = MacroEventSubscription(
        user_id=subscription_data.user_id,
        event_type=subscription_data.event_type,
        subscribed=subscription_data.subscribed,
        impact_filter=subscription_data.impact_filter
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return subscription.to_dict()


@router.delete("/subscribe/{user_id}/{event_type}")
async def unsubscribe_from_event(
    user_id: UUID,
    event_type: str,
    db: Session = Depends(get_db)
):
    """Unsubscribe from a macro event type."""
    subscription = db.query(MacroEventSubscription).filter(
        MacroEventSubscription.user_id == user_id,
        MacroEventSubscription.event_type == event_type
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription for {event_type} not found"
        )

    subscription.subscribed = False
    subscription.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": "unsubscribed",
        "event_type": event_type
    }


@router.get("/subscriptions/{user_id}")
async def get_subscriptions(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all subscriptions for a user."""
    subscriptions = db.query(MacroEventSubscription).filter(
        MacroEventSubscription.user_id == user_id
    ).all()

    return {
        "user_id": str(user_id),
        "subscriptions": [
            sub.to_dict()
            for sub in subscriptions
        ]
    }


@router.post("/subscribe-all/{user_id}")
async def subscribe_to_all_events(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Subscribe to all event types."""
    event_types = [
        "fed",
        "cpi",
        "gdp",
        "employment",
        "other"
    ]

    subscriptions = []

    for event_type in event_types:
        existing = db.query(MacroEventSubscription).filter(
            MacroEventSubscription.user_id == user_id,
            MacroEventSubscription.event_type == event_type
        ).first()

        if existing:
            existing.subscribed = True
            existing.updated_at = datetime.utcnow()
        else:
            new_sub = MacroEventSubscription(
                user_id=user_id,
                event_type=event_type,
                subscribed=True,
                impact_filter=EventImpact.HIGH
            )

            db.add(new_sub)

        subscriptions.append(event_type)

    db.commit()

    return {
        "status": "subscribed_to_all",
        "event_types": subscriptions
    }


@router.post("/unsubscribe-all/{user_id}")
async def unsubscribe_from_all_events(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Unsubscribe from all event types."""
    db.query(MacroEventSubscription).filter(
        MacroEventSubscription.user_id == user_id
    ).update({
        "subscribed": False,
        "updated_at": datetime.utcnow()
    })

    db.commit()

    return {
        "status": "unsubscribed_from_all"
    }


# ============================================
# ALERT MANAGEMENT
# ============================================

@router.post(
    "/alerts",
    response_model=MacroAlertResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_macro_alert(
    alert_data: MacroAlertCreate,
    db: Session = Depends(get_db)
):
    """Create a macro event alert."""
    existing_count = db.query(MacroEventAlert).filter(
        MacroEventAlert.user_id == alert_data.user_id,
        MacroEventAlert.status == MacroAlertStatus.ACTIVE
    ).count()

    if existing_count >= settings.MAX_ALERTS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Maximum alerts per user "
                f"({settings.MAX_ALERTS_PER_USER}) exceeded"
            )
        )

    alert = MacroEventAlert(
        user_id=alert_data.user_id,
        event_id=alert_data.event_id,
        event_type=EventType(alert_data.event_type),
        timing=EventTiming(alert_data.timing),
        impact_filter=EventImpact(alert_data.impact_filter),
        name=alert_data.name,
        description=alert_data.description,
        notify_in_app=alert_data.notify_in_app,
        notify_email=alert_data.notify_email,
        status=MacroAlertStatus.ACTIVE
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert.to_dict()


@router.get("/alerts/{user_id}")
async def get_macro_alerts(
    user_id: UUID,
    status: Optional[str] = Query(
        None,
        description="Filter by status"
    ),
    event_type: Optional[str] = Query(
        None,
        description="Filter by event type"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100
    ),
    offset: int = Query(
        0,
        ge=0
    ),
    db: Session = Depends(get_db)
):
    """Get all macro alerts for a user."""
    query = db.query(MacroEventAlert).filter(
        MacroEventAlert.user_id == user_id
    )

    if status:
        try:
            query = query.filter(
                MacroEventAlert.status == MacroAlertStatus(status)
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )

    if event_type:
        try:
            query = query.filter(
                MacroEventAlert.event_type == EventType(event_type)
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event_type: {event_type}"
            )

    total = query.count()

    alerts = (
        query
        .order_by(MacroEventAlert.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": [
            alert.to_dict()
            for alert in alerts
        ]
    }


@router.delete(
    "/alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_macro_alert(
    alert_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a macro alert."""
    alert = db.query(MacroEventAlert).filter(
        MacroEventAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Macro alert {alert_id} not found"
        )

    alert.status = MacroAlertStatus.DISABLED
    alert.updated_at = datetime.utcnow()

    db.commit()

    return None


# ============================================
# MACRO EVENT NOTIFICATIONS
# ============================================

@router.get("/notifications")
async def get_all_notifications(
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of notifications to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of notifications to skip"
    ),
    db: Session = Depends(get_db)
):
    """
    Get all macro event notifications.

    Only non-archived notifications within the configured
    notification history period are returned.

    Results are ordered from newest to oldest and support
    pagination through limit and offset.
    """
    service = MacroNotificationService(db)

    total, notifications = service.get_all_notifications(
        unread_only=False,
        limit=limit,
        offset=offset
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "notifications": [
            notification.to_dict()
            for notification in notifications
        ]
    }


@router.get("/notifications/unread")
async def get_unread_notifications(
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of unread notifications to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of unread notifications to skip"
    ),
    db: Session = Depends(get_db)
):
    """
    Get unread macro event notifications.

    Only unread, non-archived notifications within the configured
    notification history period are returned.

    Results are ordered from newest to oldest and support
    pagination through limit and offset.
    """
    service = MacroNotificationService(db)

    total, notifications = service.get_all_notifications(
        unread_only=True,
        limit=limit,
        offset=offset
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "notifications": [
            notification.to_dict()
            for notification in notifications
        ]
    }


@router.post("/notifications/read-all")
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db)
):
    """
    Mark all macro event notifications as read.

    Only unread, non-archived notifications within the configured
    notification history period are updated.

    Returns the number of notifications that were marked as read.
    """
    service = MacroNotificationService(db)

    count = service.mark_all_notifications_as_read()

    return {
        "status": "success",
        "message": "All notifications marked as read",
        "count": count
    }


@router.get("/notifications/{user_id}")
async def get_macro_notifications(
    user_id: UUID,
    unread_only: bool = Query(
        False,
        description="Filter by unread"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100
    ),
    offset: int = Query(
        0,
        ge=0
    ),
    db: Session = Depends(get_db)
):
    """Get macro event notifications for a user."""
    query = db.query(MacroEventNotification).filter(
        MacroEventNotification.user_id == user_id,
        MacroEventNotification.is_archived == False
    )

    if unread_only:
        query = query.filter(
            MacroEventNotification.read == False
        )

    total = query.count()

    notifications = (
        query
        .order_by(MacroEventNotification.sent_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "notifications": [
            n.to_dict()
            for n in notifications
        ]
    }


@router.put("/notifications/{notification_id}/read")
async def mark_macro_notification_read(
    notification_id: UUID,
    db: Session = Depends(get_db)
):
    """Mark a macro notification as read."""
    notification = db.query(MacroEventNotification).filter(
        MacroEventNotification.id == notification_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )

    notification.read = True
    notification.read_at = datetime.utcnow()

    db.commit()

    return {
        "status": "success",
        "message": "Notification marked as read"
    }


# ============================================
# UPCOMING EVENTS
# ============================================

@router.get("/events/upcoming")
async def get_upcoming_events(
    limit: int = Query(
        10,
        ge=1,
        le=50
    ),
    db: Session = Depends(get_db)
):
    """Get upcoming macro events."""
    now = datetime.utcnow()

    events = (
        db.query(MacroEventCache)
        .filter(MacroEventCache.scheduled_at > now)
        .order_by(MacroEventCache.scheduled_at)
        .limit(limit)
        .all()
    )

    return {
        "total": len(events),
        "events": [
            event.to_dict()
            for event in events
        ]
    }