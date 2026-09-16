"""Pydantic schemas for the methodology API (A4.1).

These schemas define the JSON contract for:
    - GET /api/v1/methodology

Design:
    - The models mirror the dataclasses in ``app.methodology``
      field-for-field. The endpoint converts a ``Methodology`` to
      these models via ``MethodologyResponse.model_validate(...)``
      on the dataclass's ``to_dict()`` output, so the schema stays
      a dumb container and the content lives in one module.
    - Every field carries a ``description`` so the OpenAPI docs are
      useful without a separate spec.
    - The top-level model carries a ``json_schema_extra`` example so
      Swagger UI shows a representative response.
    - ``MethodologyErrorResponse`` mirrors the pattern used by the
      other endpoints in this codebase.

Units:
    - ``bull_threshold_pct`` and ``bear_threshold_pct`` are
      percentages (e.g. 20.0 for +20%).
    - ``volatility_threshold`` is a decimal fraction (0.05 = 5%).
    - ``significance_threshold`` is a p-value (0.05 = 95%
      confidence).
"""

from typing import List

from pydantic import BaseModel, Field


# ============================================================
# SECTION MODELS
# ============================================================
class ModelSpecResponse(BaseModel):
    """One forecasting model variant."""

    name: str = Field(
        ...,
        description=(
            "Stable identifier (e.g. 'prophet_fresh')."
        ),
    )
    algorithm: str = Field(
        ...,
        description="Library the variant uses (Prophet/XGBoost/LightGBM).",
    )
    strategy: str = Field(
        ...,
        description=(
            "Training strategy: 'fresh' (full retrain), 'warm', or "
            "'incremental'."
        ),
    )
    description: str = Field(
        ...,
        description="One-sentence description of the variant.",
    )


class CorrelationSpecResponse(BaseModel):
    """How BTC-vs-macro correlations are computed."""

    method: str = Field(
        ..., description="Statistical method (e.g. 'Pearson')."
    )
    windows_days: List[int] = Field(
        ...,
        description="Rolling window lengths in days.",
    )
    strength_thresholds: dict = Field(
        ...,
        description=(
            "Cutoffs for the strength labels. ``strong_gt`` is the "
            "absolute coefficient above which a correlation is "
            "labelled strong; ``medium_gte`` is the absolute "
            "coefficient at or above which it is labelled medium."
        ),
    )
    significance_threshold: float = Field(
        ...,
        description=(
            "Two-tailed p-value below which a correlation is "
            "considered statistically significant."
        ),
    )
    indicators: List[str] = Field(
        ...,
        description="Product-facing indicator labels.",
    )
    description: str = Field(
        ..., description="Short prose description of the method."
    )


class RegimeSpecResponse(BaseModel):
    """How market regimes are classified."""

    labels: List[str] = Field(
        ..., description="The four regime labels."
    )
    priority: List[str] = Field(
        ...,
        description=(
            "Priority order when more than one label could apply "
            "(first match wins)."
        ),
    )
    bull_threshold_pct: float = Field(
        ...,
        description=(
            "Cumulative return above which a window is bull "
            "(percentage)."
        ),
    )
    bear_threshold_pct: float = Field(
        ...,
        description=(
            "Cumulative return below which a window is bear "
            "(percentage)."
        ),
    )
    volatility_threshold: float = Field(
        ...,
        description=(
            "Standard deviation of percentage returns above which a "
            "window is volatile (decimal, 0.05 = 5%)."
        ),
    )
    description: str = Field(
        ..., description="Short prose description of the method."
    )


class DataSourceSpecResponse(BaseModel):
    """One external data source cited by the methodology."""

    name: str = Field(..., description="Human-readable source name.")
    url: str = Field(
        ...,
        description=(
            "Base URL of the source, or empty for internal-only "
            "sources."
        ),
    )
    description: str = Field(
        ...,
        description="One-sentence description of what the source "
        "contributes.",
    )


class LimitationSpecResponse(BaseModel):
    """One known limitation of the methodology."""

    area: str = Field(
        ...,
        description="Short label for what the limitation concerns.",
    )
    description: str = Field(
        ..., description="One-sentence explanation."
    )


# ============================================================
# ENVELOPE
# ============================================================
class MethodologyResponse(BaseModel):
    """Response body for GET /api/v1/methodology.

    Attributes:
        version: Semver string for the methodology.
        updated_at: ISO 8601 date the content last changed.
        models: Forecasting model variants.
        correlations: Correlation method.
        regimes: Regime classification method.
        data_sources: External data sources.
        limitations: Known limitations.
    """

    version: str = Field(
        ..., description="Semver string for the methodology."
    )
    updated_at: str = Field(
        ...,
        description="ISO 8601 date the content last changed.",
    )
    models: List[ModelSpecResponse] = Field(
        default_factory=list,
        description="Forecasting model variants.",
    )
    correlations: CorrelationSpecResponse = Field(
        ..., description="Correlation method."
    )
    regimes: RegimeSpecResponse = Field(
        ..., description="Regime classification method."
    )
    data_sources: List[DataSourceSpecResponse] = Field(
        default_factory=list,
        description="External data sources.",
    )
    limitations: List[LimitationSpecResponse] = Field(
        default_factory=list,
        description="Known limitations.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "version": "1.0.0",
                    "updated_at": "2026-09-16",
                    "models": [
                        {
                            "name": "prophet_fresh",
                            "algorithm": "Prophet",
                            "strategy": "fresh",
                            "description": (
                                "Prophet retrained from scratch on "
                                "each run."
                            ),
                        }
                    ],
                    "correlations": {
                        "method": "Pearson",
                        "windows_days": [30, 90, 365],
                        "strength_thresholds": {
                            "strong_gt": 0.7,
                            "medium_gte": 0.3,
                        },
                        "significance_threshold": 0.05,
                        "indicators": [
                            "inflation",
                            "rates",
                            "gdp",
                            "unemployment",
                        ],
                        "description": (
                            "Pearson product-moment correlation "
                            "over rolling windows."
                        ),
                    },
                    "regimes": {
                        "labels": [
                            "bull",
                            "bear",
                            "volatile",
                            "neutral",
                        ],
                        "priority": [
                            "volatile",
                            "bull",
                            "bear",
                            "neutral",
                        ],
                        "bull_threshold_pct": 20.0,
                        "bear_threshold_pct": 20.0,
                        "volatility_threshold": 0.05,
                        "description": (
                            "Windows are labelled by price "
                            "trajectory; volatility takes priority."
                        ),
                    },
                    "data_sources": [
                        {
                            "name": "FRED",
                            "url": "https://fred.stlouisfed.org",
                            "description": (
                                "Federal Reserve Economic Data."
                            ),
                        }
                    ],
                    "limitations": [
                        {
                            "area": "data coverage",
                            "description": (
                                "GDP and unemployment are not yet "
                                "available."
                            ),
                        }
                    ],
                }
            ]
        }
    }


# ============================================================
# ERROR
# ============================================================
class MethodologyErrorResponse(BaseModel):
    """Response body for methodology endpoint errors.

    Attributes:
        error: Short error code.
        message: Human-readable error message.
        detail: Optional additional context.
    """

    error: str = Field(..., description="Short error code.")
    message: str = Field(
        ..., description="Human-readable message."
    )
    detail: str = Field(
        default="", description="Optional additional context."
    )


__all__ = [
    "CorrelationSpecResponse",
    "DataSourceSpecResponse",
    "LimitationSpecResponse",
    "MethodologyErrorResponse",
    "MethodologyResponse",
    "ModelSpecResponse",
    "RegimeSpecResponse",
]