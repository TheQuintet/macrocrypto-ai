"""API routes for prediction change alerts"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.database.session import SessionLocal
from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionChangeConfig,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection
)
from app.schemas.prediction_alert import (
    PredictionAlertCreate,
    PredictionAlertUpdate,
    PredictionAlertResponse
)
from app.config import settings

router = APIRouter(prefix="/api/v1/alerts/prediction", tags=["prediction-alerts"])


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# CREATE PREDICTION ALERT
# ============================================

@router.post("/", response_model=PredictionAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction_alert(
    alert_data: PredictionAlertCreate,
    db: Session = Depends(get_db)
):
    """Create a new prediction change alert."""
    # Check if user already has too many alerts
    existing_count = db.query(PredictionChangeAlert).filter(
        PredictionChangeAlert.user_id == alert_data.user_id,
        PredictionChangeAlert.status == PredictionAlertStatus.ACTIVE
    ).count()

    if existing_count >= settings.MAX_ALERTS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum alerts per user ({settings.MAX_ALERTS_PER_USER}) exceeded"
        )

    # Create alert
    alert = PredictionChangeAlert(
        user_id=alert_data.user_id,
        threshold_percent=alert_data.threshold_percent,
        horizon=PredictionHorizon(alert_data.horizon),
        direction=PredictionDirection(alert_data.direction),
        asset=alert_data.asset,
        monitor_confidence=alert_data.monitor_confidence,
        confidence_threshold_percent=alert_data.confidence_threshold_percent,
        name=alert_data.name,
        description=alert_data.description,
        notify_in_app=alert_data.notify_in_app,
        notify_email=alert_data.notify_email,
        status=PredictionAlertStatus.ACTIVE
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert.to_dict()


# ============================================
# GET PREDICTION ALERTS
# ============================================

@router.get("/", response_model=dict)
async def get_prediction_alerts(
    user_id: UUID = Query(..., description="User ID to fetch alerts for"),
    status: Optional[str] = Query(None, description="Filter by status"),
    horizon: Optional[str] = Query(None, description="Filter by horizon (24h/7d)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all prediction alerts for a user."""
    query = db.query(PredictionChangeAlert).filter(
        PredictionChangeAlert.user_id == user_id
    )

    if status:
        try:
            query = query.filter(PredictionChangeAlert.status == PredictionAlertStatus(status))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )

    if horizon:
        try:
            query = query.filter(PredictionChangeAlert.horizon == PredictionHorizon(horizon))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid horizon: {horizon}"
            )

    total = query.count()
    alerts = query.order_by(PredictionChangeAlert.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": [alert.to_dict() for alert in alerts]
    }


@router.get("/{alert_id}", response_model=PredictionAlertResponse)
async def get_prediction_alert(
    alert_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific prediction alert by ID."""
    alert = db.query(PredictionChangeAlert).filter(
        PredictionChangeAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction alert {alert_id} not found"
        )

    return alert.to_dict()


# ============================================
# UPDATE PREDICTION ALERT
# ============================================

@router.put("/{alert_id}", response_model=PredictionAlertResponse)
async def update_prediction_alert(
    alert_id: UUID,
    alert_data: PredictionAlertUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing prediction alert."""
    alert = db.query(PredictionChangeAlert).filter(
        PredictionChangeAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction alert {alert_id} not found"
        )

    # Update fields
    update_data = alert_data.model_dump(exclude_unset=True)

    if "threshold_percent" in update_data:
        alert.threshold_percent = update_data["threshold_percent"]
    if "horizon" in update_data:
        alert.horizon = PredictionHorizon(update_data["horizon"])
    if "direction" in update_data:
        alert.direction = PredictionDirection(update_data["direction"])
    if "monitor_confidence" in update_data:
        alert.monitor_confidence = update_data["monitor_confidence"]
    if "confidence_threshold_percent" in update_data:
        alert.confidence_threshold_percent = update_data["confidence_threshold_percent"]
    if "name" in update_data:
        alert.name = update_data["name"]
    if "description" in update_data:
        alert.description = update_data["description"]
    if "notify_in_app" in update_data:
        alert.notify_in_app = update_data["notify_in_app"]
    if "notify_email" in update_data:
        alert.notify_email = update_data["notify_email"]
    if "status" in update_data:
        alert.status = PredictionAlertStatus(update_data["status"])

    alert.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)

    return alert.to_dict()


# ============================================
# DELETE PREDICTION ALERT
# ============================================

@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prediction_alert(
    alert_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a prediction alert (soft delete - mark as disabled)."""
    alert = db.query(PredictionChangeAlert).filter(
        PredictionChangeAlert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction alert {alert_id} not found"
        )

    alert.status = PredictionAlertStatus.DISABLED
    alert.updated_at = datetime.utcnow()

    db.commit()

    return None


# ============================================
# USER CONFIGURATION
# ============================================

@router.get("/config/{user_id}")
async def get_prediction_config(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Get prediction alert configuration for a user."""
    config = db.query(PredictionChangeConfig).filter(
        PredictionChangeConfig.user_id == user_id
    ).first()

    if not config:
        # Return defaults
        return {
            "user_id": str(user_id),
            "default_threshold": 2.0,
            "confidence_change_threshold": 5.0,
            "default_horizon": "24h",
            "notify_in_app_default": True,
            "notify_email_default": True
        }

    return config.to_dict()


@router.put("/config/{user_id}")
async def update_prediction_config(
    user_id: UUID,
    config_data: dict,
    db: Session = Depends(get_db)
):
    """Update prediction alert configuration for a user."""
    config = db.query(PredictionChangeConfig).filter(
        PredictionChangeConfig.user_id == user_id
    ).first()

    if not config:
        config = PredictionChangeConfig(user_id=user_id)
        db.add(config)

    if "default_threshold" in config_data:
        config.default_threshold = config_data["default_threshold"]
    if "confidence_change_threshold" in config_data:
        config.confidence_change_threshold = config_data["confidence_change_threshold"]
    if "default_horizon" in config_data:
        config.default_horizon = PredictionHorizon(config_data["default_horizon"])
    if "notify_in_app_default" in config_data:
        config.notify_in_app_default = config_data["notify_in_app_default"]
    if "notify_email_default" in config_data:
        config.notify_email_default = config_data["notify_email_default"]

    config.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(config)

    return config.to_dict()