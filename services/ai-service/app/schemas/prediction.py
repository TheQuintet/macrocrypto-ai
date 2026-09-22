"""Pydantic schemas for the prediction endpoints.

These schemas define the JSON contract for:
    - GET /api/v1/predict/btc?horizon=24h

Design:
    - `PredictionPoint` — a single forecast row (ds, yhat, bounds)
    - `PredictionResponse` — the single-model response envelope
    - `TrendDirection` — enum with up/down/neutral
    - `ModelBatch` — one model's stored prediction batch (M6a)
    - `ConsensusPoint` — one timestamp of the cross-model mean (M6a)
    - `StoredComparisonPayload` — the comparison summary (M6a)
    - `ComparisonResponse` — the multi-model response envelope (M6a)

Field naming:
    - All timestamps are ISO-8601 strings (UTC), serialized by
      Pydantic from `datetime` values.
    - Prices are floats (USD).
    - Percentages are expressed as floats (e.g., 1.10 means +1.10%).
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

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


# ============================================================
# M6a — MULTI-MODEL COMPARISON SCHEMAS
# ============================================================
class ModelBatch(BaseModel):
    """One model's stored prediction batch.

    Attributes:
        model_name: Model identifier (e.g., 'prophet_fresh').
        model_version: Optional model version string, if known.
        prediction_time: When this batch was generated (UTC).
        horizon: Horizon label ('24h' or '7d').
        confidence: Confidence level of the bounds.
        predictions: Ordered list of forecast points for this model.
    """

    model_name: str = Field(
        ...,
        description="Model identifier.",
    )
    model_version: Optional[str] = Field(
        None,
        description="Model version, if known.",
    )
    prediction_time: datetime = Field(
        ...,
        description="When this batch was generated (UTC).",
    )
    horizon: str = Field(
        ...,
        description="Forecast horizon ('24h' or '7d').",
    )
    confidence: float = Field(
        ...,
        description="Confidence level (0.70, 0.85, 0.95).",
    )
    predictions: List[PredictionPoint] = Field(
        default_factory=list,
        description="Ordered list of forecast points.",
    )


class ConsensusPoint(BaseModel):
    """One timestamp of the cross-model consensus.

    Attributes:
        time: Forecast timestamp (UTC).
        predicted_price: Mean predicted price across contributing
            models (USD).
        lower_bound: Mean lower bound across contributing models
            (USD), or None if no model provided bounds.
        upper_bound: Mean upper bound across contributing models
            (USD), or None if no model provided bounds.
        contributing_models: Number of models that contributed a
            prediction at this timestamp (always >= 2).
    """

    time: datetime = Field(
        ...,
        description="Forecast timestamp (UTC).",
    )
    predicted_price: float = Field(
        ...,
        description="Mean predicted price across models (USD).",
    )
    lower_bound: Optional[float] = Field(
        None,
        description="Mean lower bound across models (USD).",
    )
    upper_bound: Optional[float] = Field(
        None,
        description="Mean upper bound across models (USD).",
    )
    contributing_models: int = Field(
        ...,
        description="Number of models contributing at this timestamp.",
    )


class StoredComparisonPayload(BaseModel):
    """Summary of a stored-prediction comparison.

    Attributes:
        models_compared: Models that contributed at least one
            consensus point.
        models_missing: Models that were requested but either had no
            stored predictions or did not overlap with any other
            requested model.
        agreement_score: Score in [0, 1]. 1.0 means all models
            predict the same value at every compared timestamp; 0
            means the spread is as large as the mean. When fewer
            than two models contribute, this is 1.0 (single-model
            degenerate case).
        best_model: The model with the lowest MAE in the recent
            window. May not be one of `models_compared` — it
            reflects the overall best, not "best among compared".
            None if no model has a recent MAE.
        timestamps_compared: Number of timestamps included in the
            consensus.
    """

    models_compared: List[str] = Field(
        default_factory=list,
        description="Models that contributed to the consensus.",
    )
    models_missing: List[str] = Field(
        default_factory=list,
        description="Requested models without usable data.",
    )
    agreement_score: float = Field(
        ...,
        description="Agreement score in [0, 1].",
    )
    best_model: Optional[str] = Field(
        None,
        description="Best model by recent MAE (may not be in comparison).",
    )
    timestamps_compared: int = Field(
        ...,
        description="Number of timestamps in the consensus.",
    )


class ComparisonResponse(BaseModel):
    """Response body for GET /api/v1/predict/btc with ?models=...

    Returned when the caller requests two or more models. The
    single-model request path continues to return `PredictionResponse`.

    Attributes:
        horizon: Requested horizon ('24h' or '7d').
        confidence: Confidence level of the bounds.
        current_price: Latest known BTC price (USD), or None.
        models: Mapping of model_name → ModelBatch. Only models that
            had stored predictions appear here.
        comparison: Consensus, agreement score, and best model.
        missing_models: Requested model names that produced no data.
            Mirrors `comparison.models_missing` for convenience.
        generated_at: When this response was produced (UTC).
    """

    horizon: str = Field(
        ...,
        description="Forecast horizon ('24h' or '7d').",
    )
    confidence: float = Field(
        ...,
        description="Confidence level of the bounds.",
    )
    current_price: Optional[float] = Field(
        None,
        description="Latest known BTC price in USD.",
    )
    models: Dict[str, ModelBatch] = Field(
        default_factory=dict,
        description="Model name → its stored prediction batch.",
    )
    comparison: StoredComparisonPayload = Field(
        ...,
        description="Consensus, agreement, and best-model summary.",
    )
    missing_models: List[str] = Field(
        default_factory=list,
        description="Requested models without stored predictions.",
    )
    generated_at: datetime = Field(
        ...,
        description="When this response was produced (UTC).",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "horizon": "24h",
                    "confidence": 0.85,
                    "current_price": 63500.42,
                    "models": {
                        "prophet": {
                            "model_name": "prophet",
                            "model_version": "1.0.0",
                            "prediction_time": "2026-09-14T12:00:00Z",
                            "horizon": "24h",
                            "confidence": 0.85,
                            "predictions": [
                                {
                                    "time": "2026-09-14T13:00:00Z",
                                    "predicted_price": 63550.10,
                                    "lower_bound": 63400.00,
                                    "upper_bound": 63700.20,
                                }
                            ],
                        }
                    },
                    "comparison": {
                        "models_compared": ["prophet", "xgboost_fresh"],
                        "models_missing": [],
                        "agreement_score": 0.98,
                        "best_model": "prophet",
                        "timestamps_compared": 24,
                    },
                    "missing_models": [],
                    "generated_at": "2026-09-14T12:00:00Z",
                }
            ]
        }
    }