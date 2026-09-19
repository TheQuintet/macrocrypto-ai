"""Pydantic schemas for the prediction endpoints.

These schemas define the JSON contract for:
    - GET /api/v1/predict/btc?horizon=24h

Design:
    - `PredictionPoint` — a single forecast row (ds, yhat, bounds)
    - `PredictionResponse` — the full response envelope
    - `TrendDirection` — enum with up/down/neutral

Field naming:
    - All timestamps are ISO-8601 strings (UTC), serialized by
      Pydantic from `datetime` values.
    - Prices are floats (USD).
    - Percentages are expressed as floats (e.g., 1.10 means +1.10%).
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# ENUMS
# ============================================================
class TrendDirection(str, Enum):
    """Trend direction of the forecast.

    Values:
        UP: Predicted price change exceeds the positive threshold.
        DOWN: Predicted price change is below the negative threshold.
        NEUTRAL: Predicted price change is within the neutral band.
    """

    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


# ============================================================
# SCHEMAS
# ============================================================
class PredictionPoint(BaseModel):
    """A single forecast point.

    Attributes:
        time: The forecast timestamp (when the price is predicted FOR).
        predicted_price: The point forecast (USD).
        lower_bound: Lower confidence bound (USD).
        upper_bound: Upper confidence bound (USD).
    """

    time: datetime = Field(
        ...,
        description="Forecast timestamp (UTC, ISO-8601).",
    )
    predicted_price: float = Field(
        ...,
        description="Predicted BTC price in USD.",
    )
    lower_bound: float = Field(
        ...,
        description="Lower confidence bound in USD.",
    )
    upper_bound: float = Field(
        ...,
        description="Upper confidence bound in USD.",
    )


class PredictionResponse(BaseModel):
    """Response body for GET /api/v1/predict/btc.

    Contains:
        - Metadata: horizon, model name, confidence, prediction time
        - Current price + summary metrics (predicted end price,
          percentage change, trend direction)
        - The full list of forecast points

    Attributes:
        horizon: The requested horizon (e.g., "24h").
        model_name: The model that produced the predictions.
        confidence: The confidence level of the bounds (0.70/0.85/0.95).
        prediction_time: When the prediction batch was generated.
        current_price: Latest known BTC price (USD). None if no
            current price is available.
        predicted_end_price: Predicted price at the end of the
            horizon (the last forecast point).
        price_change_pct: Percentage change from current price to
            predicted end price. None if current price is None.
        trend: Trend direction derived from price_change_pct.
        predictions: Full list of forecast points.
    """

    horizon: str = Field(
        ...,
        description="Forecast horizon, e.g. '24h' or '7d'.",
    )
    model_name: str = Field(
        ...,
        description="Model that produced the predictions.",
    )
    confidence: float = Field(
        ...,
        description="Confidence level of the bounds (0.70, 0.85, 0.95).",
    )
    prediction_time: datetime = Field(
        ...,
        description="When the prediction batch was generated (UTC).",
    )
    current_price: Optional[float] = Field(
        None,
        description=(
            "Latest known BTC price in USD. Null if no recent price "
            "is available from the data source."
        ),
    )
    predicted_end_price: float = Field(
        ...,
        description="Predicted price at the end of the horizon (USD).",
    )
    price_change_pct: Optional[float] = Field(
        None,
        description=(
            "Percentage change from current_price to "
            "predicted_end_price. Null if current_price is null."
        ),
    )
    trend: TrendDirection = Field(
        ...,
        description="Trend direction: up, down, or neutral.",
    )
    predictions: List[PredictionPoint] = Field(
        ...,
        description="Ordered list of forecast points.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "horizon": "24h",
                    "model_name": "prophet",
                    "confidence": 0.85,
                    "prediction_time": "2026-09-14T12:00:00Z",
                    "current_price": 63500.42,
                    "predicted_end_price": 64200.75,
                    "price_change_pct": 1.10,
                    "trend": "up",
                    "predictions": [
                        {
                            "time": "2026-09-14T13:00:00Z",
                            "predicted_price": 63550.10,
                            "lower_bound": 63400.00,
                            "upper_bound": 63700.20,
                        }
                    ],
                }
            ]
        }
    }


class PredictionErrorResponse(BaseModel):
    """Response body for prediction endpoint errors.

    Returned when the endpoint cannot produce a response (e.g.,
    no predictions exist yet, or the query parameters are invalid).

    Attributes:
        error: Short error code (e.g., "no_predictions").
        message: Human-readable error message.
        detail: Optional additional context.
    """

    error: str = Field(
        ...,
        description="Short error code.",
    )
    message: str = Field(
        ...,
        description="Human-readable error message.",
    )
    detail: Optional[str] = Field(
        None,
        description="Optional additional context.",
    )