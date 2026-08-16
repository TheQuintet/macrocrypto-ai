"""Prediction alert schemas for API requests/responses"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class PredictionAlertCreate(BaseModel):
    """Schema for creating a prediction alert."""
    user_id: UUID
    threshold_percent: float = Field(..., gt=0, le=10, description="1% to 10%")
    horizon: str = Field(..., description="24h or 7d")
    direction: str = Field(default="both", description="up, down, or both")
    asset: str = Field(default="BTC/USD")
    monitor_confidence: bool = True
    confidence_threshold_percent: float = Field(default=5.0, ge=0, le=20)
    name: Optional[str] = None
    description: Optional[str] = None
    notify_in_app: bool = True
    notify_email: bool = True

    @validator('horizon')
    def validate_horizon(cls, v):
        valid_horizons = ['24h', '7d']
        if v not in valid_horizons:
            raise ValueError(f'horizon must be one of: {", ".join(valid_horizons)}')
        return v

    @validator('direction')
    def validate_direction(cls, v):
        valid_directions = ['up', 'down', 'both']
        if v not in valid_directions:
            raise ValueError(f'direction must be one of: {", ".join(valid_directions)}')
        return v


class PredictionAlertUpdate(BaseModel):
    """Schema for updating a prediction alert."""
    threshold_percent: Optional[float] = Field(None, gt=0, le=10)
    horizon: Optional[str] = None
    direction: Optional[str] = None
    monitor_confidence: Optional[bool] = None
    confidence_threshold_percent: Optional[float] = Field(None, ge=0, le=20)
    name: Optional[str] = None
    description: Optional[str] = None
    notify_in_app: Optional[bool] = None
    notify_email: Optional[bool] = None
    status: Optional[str] = None

    @validator('horizon')
    def validate_horizon(cls, v):
        if v is not None:
            valid_horizons = ['24h', '7d']
            if v not in valid_horizons:
                raise ValueError(f'horizon must be one of: {", ".join(valid_horizons)}')
        return v

    @validator('direction')
    def validate_direction(cls, v):
        if v is not None:
            valid_directions = ['up', 'down', 'both']
            if v not in valid_directions:
                raise ValueError(f'direction must be one of: {", ".join(valid_directions)}')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ['active', 'disabled', 'expired']
            if v not in valid_statuses:
                raise ValueError(f'status must be one of: {", ".join(valid_statuses)}')
        return v


class PredictionAlertResponse(BaseModel):
    """Schema for prediction alert response."""
    id: str
    user_id: str
    threshold_percent: float
    horizon: str
    direction: str
    asset: str
    monitor_confidence: bool
    confidence_threshold_percent: float
    status: str
    created_at: str
    updated_at: str
    triggered_at: Optional[str]
    notify_in_app: bool
    notify_email: bool
    name: Optional[str]
    description: Optional[str]