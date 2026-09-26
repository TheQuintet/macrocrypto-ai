"""API routes for alert management"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database.session import SessionLocal
from app.models.alert import HistoryEventType, PriceAlert, AlertStatus, AlertType, AlertHistory
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertListResponse
from app.services.alert_engine import AlertEngine
from app.config import settings

router = APIRouter(prefix="/api/v1/alerts", tags=["price-alerts"])


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# CREATE ALERT
# ============================================

@router.post("/price", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_price_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    """Create a new price alert."""
    # Check if user already has too many alerts
    existing_count = db.query(PriceAlert).filter(
        PriceAlert.user_id == alert_data.user_id,
        PriceAlert.status == AlertStatus.ACTIVE
    ).count()
    
    if existing_count >= settings.MAX_ALERTS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum alerts per user ({settings.MAX_ALERTS_PER_USER}) exceeded"
        )
    
    # Create alert
    alert = PriceAlert(
        user_id=alert_data.user_id,
        threshold_price=alert_data.threshold_price,
        alert_type=AlertType(alert_data.alert_type),
        asset=alert_data.asset,
        one_time=alert_data.one_time,
        name=alert_data.name,
        description=alert_data.description,
        notify_in_app=alert_data.notify_in_app,
        notify_email=alert_data.notify_email,
        status=AlertStatus.ACTIVE
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Create history entry
    history = AlertHistory(
        alert_id=alert.id,
        event_type=HistoryEventType.CREATED,
        event_source="user",
        previous_status=None,
        new_status=AlertStatus.ACTIVE,
        triggered_at=datetime.utcnow()
    )
    db.add(history)
    db.commit()
    
    return alert.to_dict()


# ============================================
# GET ALERTS
# ============================================

@router.get("/price", response_model=AlertListResponse)
async def get_price_alerts(
    user_id: UUID = Query(..., description="User ID to fetch alerts for"),
    status: Optional[str] = Query(None, description="Filter by status"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all price alerts for a user."""
    query = db.query(PriceAlert).filter(PriceAlert.user_id == user_id)
    
    if status:
        try:
            query = query.filter(PriceAlert.status == AlertStatus(status))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    if alert_type:
        try:
            query = query.filter(PriceAlert.alert_type == AlertType(alert_type))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid alert_type: {alert_type}"
            )
    
    total = query.count()
    alerts = query.order_by(PriceAlert.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": [alert.to_dict() for alert in alerts]
    }


@router.get("/price/{alert_id}", response_model=AlertResponse)
async def get_price_alert(
    alert_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific price alert by ID."""
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    return alert.to_dict()


# ============================================
# UPDATE ALERT
# ============================================

@router.put("/price/{alert_id}", response_model=AlertResponse)
async def update_price_alert(
    alert_id: UUID,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing price alert."""
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    # Store previous status for history
    previous_status = alert.status
    
    # Update fields
    update_data = alert_data.model_dump(exclude_unset=True)
    
    if "threshold_price" in update_data:
        alert.threshold_price = update_data["threshold_price"]
    if "alert_type" in update_data:
        alert.alert_type = AlertType(update_data["alert_type"])
    if "asset" in update_data:
        alert.asset = update_data["asset"]
    if "one_time" in update_data:
        alert.one_time = update_data["one_time"]
    if "name" in update_data:
        alert.name = update_data["name"]
    if "description" in update_data:
        alert.description = update_data["description"]
    if "notify_in_app" in update_data:
        alert.notify_in_app = update_data["notify_in_app"]
    if "notify_email" in update_data:
        alert.notify_email = update_data["notify_email"]
    if "status" in update_data:
        alert.status = AlertStatus(update_data["status"])
    
    alert.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    
    # Create history entry for status change
    if alert.status != previous_status:
        history = AlertHistory(
            alert_id=alert.id,
            event_type=HistoryEventType.UPDATED,
            event_source="user",
            previous_status=previous_status,
            new_status=alert.status,
            triggered_at=datetime.utcnow()
        )
        db.add(history)
        db.commit()
    
    return alert.to_dict()


# ============================================
# DELETE ALERT
# ============================================

@router.delete("/price/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_alert(
    alert_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a price alert (hard delete). Pause uses PUT status=disabled."""
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )

    db.delete(alert)
    db.commit()
    
    return None


# ============================================
# TRIGGER ALERT MANUALLY (for testing)
# ============================================

@router.post("/price/{alert_id}/trigger", response_model=AlertResponse)
async def trigger_alert_manually(
    alert_id: UUID,
    db: Session = Depends(get_db)
):
    """Manually trigger an alert (for testing purposes)."""
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    
    if alert.status != AlertStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alert is not active (current status: {alert.status.value})"
        )
    
    # Use the alert's threshold price as the trigger price
    engine = AlertEngine(db)
    engine._handle_triggered_alert(alert, alert.threshold_price)
    
    db.refresh(alert)
    return alert.to_dict()