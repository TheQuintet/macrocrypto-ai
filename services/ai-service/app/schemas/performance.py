"""Pydantic schemas for the performance API.

These schemas define the JSON contract for:
    - GET /api/v1/performance/btc

Design:
    - `PerformanceMetrics` — the aggregate error metrics for one
      (model, horizon) entry
    - `MarketBreakdownEntry` — per-market-condition metrics
    - `ThresholdStatus` — per-metric threshold check result
    - `PerformanceEntry` — one (model, horizon) row
    - `PerformanceResponse` — the full envelope with all entries

Units:
    - `mae` and `rmse` are in USD (as stored in prediction_performance)
    - `mape` and `directional_accuracy` are in percent
    - Threshold `value` and `threshold` follow the metric's unit
      (MAE/RMSE thresholds are in percent-of-mean-price; the check
      normalizes them internally — see app.ai.thresholds)
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# METRICS
# ============================================================
class PerformanceMetrics(BaseModel):
    """Aggregate error metrics for one (model, horizon).

    Attributes:
        mae: Mean Absolute Error in USD.
        rmse: Root Mean Square Error in USD.
        mape: Mean Absolute Percentage Error (percent).
        directional_accuracy: Percentage of correct direction
            predictions (0-100).
    """

    mae: Optional[float] = Field(None, description="MAE in USD.")
    rmse: Optional[float] = Field(None, description="RMSE in USD.")
    mape: Optional[float] = Field(None, description="MAPE in percent.")
    directional_accuracy: Optional[float] = Field(
        None,
        description="Directional accuracy in percent (0-100).",
    )


# ============================================================
# MARKET BREAKDOWN
# ============================================================
class MarketBreakdownEntry(BaseModel):
    """Aggregate metrics for one market condition bucket.

    Attributes:
        mae: Mean MAE across rows in this bucket.
        rmse: Mean RMSE across rows in this bucket.
        mape: Mean MAPE across rows in this bucket.
        samples: Number of rows in this bucket.
    """

    mae: Optional[float] = Field(None, description="MAE in USD.")
    rmse: Optional[float] = Field(None, description="RMSE in USD.")
    mape: Optional[float] = Field(None, description="MAPE in percent.")
    samples: int = Field(0, description="Number of evaluated points.")


# ============================================================
# THRESHOLD STATUS
# ============================================================
class ThresholdStatus(BaseModel):
    """Status of one metric against its configured threshold.

    Attributes:
        metric: Metric identifier ('mae_pct', 'rmse_pct', 'mape',
            'directional_accuracy').
        value: The metric's actual value.
        threshold: The configured threshold.
        breached: True if the value crossed the threshold.
        breach_direction: 'above' for error metrics, 'below' for
            directional accuracy.
    """

    metric: str = Field(..., description="Metric identifier.")
    value: float = Field(..., description="Actual value.")
    threshold: float = Field(..., description="Configured threshold.")
    breached: bool = Field(
        ..., description="True if the metric is out of bounds."
    )
    breach_direction: str = Field(
        ...,
        description="'above' for error metrics, 'below' for accuracy.",
    )


# ============================================================
# ENTRY
# ============================================================
class PerformanceEntry(BaseModel):
    """Full performance record for one (model, horizon) pair.

    Attributes:
        model_name: Model identifier (e.g. 'prophet_fresh').
        model_version: Version string.
        horizon: '24h' or '7d'.
        samples: Total matched points in the window.
        metrics: Aggregate error metrics.
        market_breakdown: Per-condition breakdown (may be empty).
        thresholds: Per-metric threshold status (may be empty).
        recent_breach_count: Number of threshold breaches recorded
            for this (model, horizon) in the window.
        last_updated: Newest forecast_date in the window.
    """

    model_name: str = Field(..., description="Model identifier.")
    model_version: Optional[str] = Field(
        None, description="Model version."
    )
    horizon: str = Field(..., description="'24h' or '7d'.")
    samples: int = Field(0, description="Matched evaluation points.")
    metrics: PerformanceMetrics = Field(
        ..., description="Aggregate error metrics."
    )
    market_breakdown: Dict[str, MarketBreakdownEntry] = Field(
        default_factory=dict,
        description="Per-market-condition metrics.",
    )
    thresholds: List[ThresholdStatus] = Field(
        default_factory=list,
        description="Per-metric threshold status.",
    )
    recent_breach_count: int = Field(
        0, description="Breaches recorded in the window."
    )
    last_updated: Optional[datetime] = Field(
        None, description="Newest forecast_date in the window."
    )


# ============================================================
# ENVELOPE
# ============================================================
class PerformanceResponse(BaseModel):
    """Response body for GET /api/v1/performance/btc.

    Attributes:
        time_period_days: Look-back window in days.
        generated_at: When this response was produced (UTC).
        entries: One entry per (model, horizon) pair.
    """

    time_period_days: int = Field(
        ..., description="Look-back window in days."
    )
    generated_at: datetime = Field(
        ..., description="When this response was produced."
    )
    entries: List[PerformanceEntry] = Field(
        default_factory=list,
        description="One entry per (model, horizon) pair.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "time_period_days": 30,
                    "generated_at": "2026-09-14T12:00:00Z",
                    "entries": [
                        {
                            "model_name": "prophet_fresh",
                            "model_version": "1.0.0",
                            "horizon": "24h",
                            "samples": 720,
                            "metrics": {
                                "mae": 500.0,
                                "rmse": 700.0,
                                "mape": 1.2,
                                "directional_accuracy": 62.5,
                            },
                            "market_breakdown": {
                                "bull": {
                                    "mae": 450.0,
                                    "rmse": 600.0,
                                    "mape": 1.0,
                                    "samples": 300,
                                }
                            },
                            "thresholds": [
                                {
                                    "metric": "mae_pct",
                                    "value": 1.0,
                                    "threshold": 10.0,
                                    "breached": False,
                                    "breach_direction": "above",
                                }
                            ],
                            "recent_breach_count": 0,
                            "last_updated": "2026-09-14T11:00:00Z",
                        }
                    ],
                }
            ]
        }
    }


class PerformanceErrorResponse(BaseModel):
    """Response body for performance endpoint errors.

    Attributes:
        error: Short error code.
        message: Human-readable error message.
        detail: Optional additional context.
    """

    error: str = Field(..., description="Short error code.")
    message: str = Field(..., description="Human-readable message.")
    detail: Optional[str] = Field(
        None, description="Optional additional context."
    )