# app/schemas/events.py
"""Shared event schemas - IDENTICAL in all services"""

from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any
from datetime import datetime


class BaseEvent(BaseModel):
    """Base event for all services"""
    event_id: str
    event_type: str
    timestamp: datetime
    source: str
    data: Dict[str, Any]


class PriceUpdatedEvent(BaseEvent):
    """Price update event from Data Service"""
    event_type: Literal["price_updated"] = "price_updated"
    source: Literal["data_service"] = "data_service"
    data: Dict[str, Any]  # Contains symbol, price, change_24h, etc.


class IndicatorUpdatedEvent(BaseEvent):
    """Economic indicator update event from Data Service"""
    event_type: Literal["indicator_updated"] = "indicator_updated"
    source: Literal["data_service"] = "data_service"
    data: Dict[str, Any]  # Contains indicator_type, value, date, etc.


class AlertTriggeredEvent(BaseEvent):
    """Alert triggered event from Alert Service"""
    event_type: Literal["alert_triggered"] = "alert_triggered"
    source: Literal["alert_service"] = "alert_service"
    data: Dict[str, Any]  # Contains alert_id, user_id, condition, etc.