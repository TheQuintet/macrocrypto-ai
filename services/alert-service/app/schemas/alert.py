"""Alert schemas for API requests/responses"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class AlertCreate(BaseModel):
    """Schema for creating a price alert."""
    user_id: UUID
    threshold_price: float = Field(..., gt=0, description="Price threshold for alert")
    alert_type: str = Field(..., description="reaches, crosses_above, crosses_below")
    asset: str = Field(default="BTC/USD")
    one_time: bool = Field(default=True, description="True = one-time, False = recurring")
    name: Optional[str] = None
    description: Optional[str] = None
    notify_in_app: bool = True
    notify_email: bool = True
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        valid_types = ['reaches', 'crosses_above', 'crosses_below']
        if v not in valid_types:
            raise ValueError(f'alert_type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('threshold_price')
    def validate_threshold(cls, v):
        if v <= 0:
            raise ValueError('threshold_price must be greater than 0')
        return v


class AlertUpdate(BaseModel):
    """Schema for updating a price alert."""
    threshold_price: Optional[float] = Field(None, gt=0)
    alert_type: Optional[str] = None
    asset: Optional[str] = None
    one_time: Optional[bool] = None
    name: Optional[str] = None
    description: Optional[str] = None
    notify_in_app: Optional[bool] = None
    notify_email: Optional[bool] = None
    status: Optional[str] = None
    
    @validator('alert_type')
    def validate_alert_type(cls, v):
        if v is not None:
            valid_types = ['reaches', 'crosses_above', 'crosses_below']
            if v not in valid_types:
                raise ValueError(f'alert_type must be one of: {", ".join(valid_types)}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = ['active', 'disabled', 'expired']
            if v not in valid_statuses:
                raise ValueError(f'status must be one of: {", ".join(valid_statuses)}')
        return v


class AlertResponse(BaseModel):
    """Schema for alert response."""
    id: str
    user_id: str
    threshold_price: float
    alert_type: str
    asset: str
    status: str
    one_time: bool
    created_at: str
    updated_at: str
    triggered_at: Optional[str]
    notify_in_app: bool
    notify_email: bool
    name: Optional[str]
    description: Optional[str]


class AlertListResponse(BaseModel):
    """Schema for list of alerts."""
    total: int
    limit: int
    offset: int
    alerts: List[Dict[str, Any]]