"""AI Service — Pydantic schemas.

This package contains the request and response schemas for the
AI Service's HTTP API. Schemas are the service's public contract
and are used both for runtime validation and OpenAPI documentation.

Available modules:
    - prediction: Prediction endpoint request/response schemas
    - performance: Performance endpoint request/response schemas
"""

from app.schemas.prediction import (
    PredictionPoint,
    PredictionResponse,
    TrendDirection,
)
from app.schemas.performance import (
    MarketBreakdownEntry,
    PerformanceEntry,
    PerformanceErrorResponse,
    PerformanceMetrics,
    PerformanceResponse,
    ThresholdStatus,
)

__all__ = [
    "PredictionPoint",
    "PredictionResponse",
    "TrendDirection",
    "MarketBreakdownEntry",
    "PerformanceEntry",
    "PerformanceErrorResponse",
    "PerformanceMetrics",
    "PerformanceResponse",
    "ThresholdStatus",
]