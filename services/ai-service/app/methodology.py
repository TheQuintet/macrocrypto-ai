"""Methodology documentation for the AI Service (A4.1).

This module is the canonical, machine-readable description of how
the AI Service produces its predictions, correlations, and regime
labels. It exists so the methodology can be served via the API
(A4.1) without duplicating prose across documentation files, and so
A4.2's version tracking has a single structured object to version.

Design:

    - Pure data. Every section is a frozen dataclass. The module
      has no I/O, no dependencies on settings, and no imports from
      the rest of the app. ``build_methodology()`` returns the
      canonical instance; call sites go through it so that a future
      branch (A4.2) can swap it for a lookup against a versioned
      registry without changing any caller.
    - Values are the source of truth. Every threshold, window,
      label, and identifier in here mirrors a constant that the
      running code uses — ``WINDOWS`` and ``SIGNIFICANCE_THRESHOLD``
      in ``app.correlation.calculator``, the regime labels in
      ``app.prediction.market``, the data sources in
      ``app.export.metadata``. The tests in Group 3 assert that the
      two agree, so drift fails loudly.
    - Version is a semver string. A4.1 hard-codes ``"1.0.0"``. A4.2
      will source it from a version registry; the field stays the
      same so the response shape does not change.
    - The ``to_dict`` methods produce JSON-serializable output.
      Nested dataclasses are converted recursively.

Not in this module:

    - The response envelope (``MethodologyResponse``) — that lives
      in ``app.schemas.methodology``.
    - The endpoint itself — that lives in
      ``app.api.v1.methodology``.
    - Changelog / version history — deferred to A4.2.
"""

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


# ============================================================
# SECTION DATACLASSES
# ============================================================
@dataclass(frozen=True)
class ModelSpec:
    """One forecasting model variant shipped by the AI Service.

    Attributes:
        name: Stable identifier (e.g. "prophet_fresh").
        algorithm: Which library the variant uses.
        strategy: How the variant trains — "fresh" for a full
            retrain, "warm" or "incremental" for updating a
            previously trained model.
        description: One-sentence description of what makes this
            variant different.
    """

    name: str
    algorithm: str
    strategy: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict."""
        return asdict(self)


@dataclass(frozen=True)
class CorrelationSpec:
    """How BTC-vs-macro correlations are computed.

    Attributes:
        method: Name of the statistical method ("Pearson").
        windows_days: Rolling window lengths in days.
        strength_thresholds: Cutoffs for "strong"/"medium"/"weak"
            labels, as (strong_gt, medium_gte) on |coefficient|.
        significance_threshold: Two-tailed p-value below which a
            correlation is significant.
        indicators: Product-facing indicator labels.
        description: Short prose description of the method.
    """

    method: str
    windows_days: Tuple[int, ...]
    strength_thresholds: Tuple[float, float]
    significance_threshold: float
    indicators: Tuple[str, ...]
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict.

        Tuples are converted to lists so the result serializes
        cleanly through pydantic and ``json.dumps``.
        """
        return {
            "method": self.method,
            "windows_days": list(self.windows_days),
            "strength_thresholds": {
                "strong_gt": self.strength_thresholds[0],
                "medium_gte": self.strength_thresholds[1],
            },
            "significance_threshold": self.significance_threshold,
            "indicators": list(self.indicators),
            "description": self.description,
        }


@dataclass(frozen=True)
class RegimeSpec:
    """How market regimes are classified.

    Attributes:
        labels: The four regime labels.
        priority: Priority order when more than one label could
            apply (first match wins).
        bull_threshold_pct: Cumulative return above which a window
            is labelled "bull".
        bear_threshold_pct: Cumulative return below which a window
            is labelled "bear".
        volatility_threshold: Standard deviation of percentage
            returns above which a window is labelled "volatile".
        description: Short prose description of the method.
    """

    labels: Tuple[str, ...]
    priority: Tuple[str, ...]
    bull_threshold_pct: float
    bear_threshold_pct: float
    volatility_threshold: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict."""
        return {
            "labels": list(self.labels),
            "priority": list(self.priority),
            "bull_threshold_pct": self.bull_threshold_pct,
            "bear_threshold_pct": self.bear_threshold_pct,
            "volatility_threshold": self.volatility_threshold,
            "description": self.description,
        }


@dataclass(frozen=True)
class DataSourceSpec:
    """One external data source cited by the methodology.

    Attributes:
        name: Human-readable source name (e.g. "FRED").
        url: Base URL of the source, or empty for internal-only
            sources.
        description: One-sentence description of what the source
            contributes.
    """

    name: str
    url: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict."""
        return asdict(self)


@dataclass(frozen=True)
class LimitationSpec:
    """One known limitation of the methodology.

    Attributes:
        area: Short label for what the limitation concerns
            (e.g. "data coverage").
        description: One-sentence explanation.
    """

    area: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict."""
        return asdict(self)


@dataclass(frozen=True)
class Methodology:
    """The full methodology documentation.

    Attributes:
        version: Semver string for the methodology.
        updated_at: ISO 8601 date the content last changed.
        models: Forecasting model variants.
        correlations: Correlation method.
        regimes: Regime classification method.
        data_sources: External data sources.
        limitations: Known limitations.
    """

    version: str
    updated_at: str
    models: List[ModelSpec] = field(default_factory=list)
    correlations: CorrelationSpec = field(
        default_factory=lambda: CorrelationSpec(
            method="",
            windows_days=(),
            strength_thresholds=(0.0, 0.0),
            significance_threshold=0.0,
            indicators=(),
            description="",
        )
    )
    regimes: RegimeSpec = field(
        default_factory=lambda: RegimeSpec(
            labels=(),
            priority=(),
            bull_threshold_pct=0.0,
            bear_threshold_pct=0.0,
            volatility_threshold=0.0,
            description="",
        )
    )
    data_sources: List[DataSourceSpec] = field(default_factory=list)
    limitations: List[LimitationSpec] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict.

        Nested dataclasses are converted via their own ``to_dict``
        so the tuple-to-list conversion in the section dataclasses
        is respected.
        """
        return {
            "version": self.version,
            "updated_at": self.updated_at,
            "models": [m.to_dict() for m in self.models],
            "correlations": self.correlations.to_dict(),
            "regimes": self.regimes.to_dict(),
            "data_sources": [s.to_dict() for s in self.data_sources],
            "limitations": [l.to_dict() for l in self.limitations],
        }


# ============================================================
# CANONICAL CONTENT
# ============================================================
# Every value below mirrors a constant or behavior in the running
# code. If the code changes, this module must change with it — the
# tests in test_methodology.py assert the correspondence.
CANONICAL_MODELS: Tuple[ModelSpec, ...] = (
    ModelSpec(
        name="prophet_fresh",
        algorithm="Prophet",
        strategy="fresh",
        description=(
            "Prophet retrained from scratch on each run; robust to "
            "missing data and weekly seasonality."
        ),
    ),
    ModelSpec(
        name="prophet_warm",
        algorithm="Prophet",
        strategy="warm",
        description=(
            "Prophet warm-started from the previous run's model; "
            "faster to converge, may drift over time."
        ),
    ),
    ModelSpec(
        name="xgboost_fresh",
        algorithm="XGBoost",
        strategy="fresh",
        description=(
            "Gradient-boosted trees retrained from scratch; uses "
            "the 10 base features plus 6 engineered lag/return "
            "features."
        ),
    ),
    ModelSpec(
        name="xgboost_incremental",
        algorithm="XGBoost",
        strategy="incremental",
        description=(
            "XGBoost updated on new data while preserving previously "
            "learned trees."
        ),
    ),
    ModelSpec(
        name="lightgbm_fresh",
        algorithm="LightGBM",
        strategy="fresh",
        description=(
            "Gradient-boosted trees retrained from scratch; similar "
            "feature set to XGBoost but a different learning "
            "algorithm."
        ),
    ),
    ModelSpec(
        name="lightgbm_incremental",
        algorithm="LightGBM",
        strategy="incremental",
        description=(
            "LightGBM updated on new data while preserving "
            "previously learned trees."
        ),
    ),
)

CANONICAL_CORRELATIONS = CorrelationSpec(
    method="Pearson",
    windows_days=(30, 90, 365),
    strength_thresholds=(0.7, 0.3),
    significance_threshold=0.05,
    indicators=("inflation", "rates", "gdp", "unemployment"),
    description=(
        "Pearson product-moment correlation between BTC daily close "
        "and each macro indicator over rolling 30-, 90-, and "
        "365-day windows. Strength and direction labels are derived "
        "from the coefficient; significance is derived from the "
        "two-tailed p-value."
    ),
)

CANONICAL_REGIMES = RegimeSpec(
    labels=("bull", "bear", "volatile", "neutral"),
    priority=("volatile", "bull", "bear", "neutral"),
    bull_threshold_pct=20.0,
    bear_threshold_pct=20.0,
    volatility_threshold=0.05,
    description=(
        "Windows are labelled by their price trajectory. Volatility "
        "takes priority over direction: a window whose standard "
        "deviation of percentage returns exceeds 5% is labelled "
        "'volatile' even if it also qualifies as bull or bear."
    ),
)

CANONICAL_DATA_SOURCES: Tuple[DataSourceSpec, ...] = (
    DataSourceSpec(
        name="FRED",
        url="https://fred.stlouisfed.org",
        description=(
            "Federal Reserve Economic Data — CPI, interest rate, "
            "M2 growth, DXY, treasury yield."
        ),
    ),
    DataSourceSpec(
        name="CoinGecko",
        url="https://www.coingecko.com",
        description=(
            "BTC price, volume, market dominance, active addresses."
        ),
    ),
    DataSourceSpec(
        name="MacroCrypto AI Service",
        url="",
        description=(
            "Derived outputs: predictions, correlations, regime "
            "labels."
        ),
    ),
)

CANONICAL_LIMITATIONS: Tuple[LimitationSpec, ...] = (
    LimitationSpec(
        area="data coverage",
        description=(
            "Two macro indicators (GDP and unemployment) do not yet "
            "have source columns in the AI Service's read tables; "
            "their correlations are skipped until the Data "
            "Ingestion Service provides them."
        ),
    ),
    LimitationSpec(
        area="horizon",
        description=(
            "Forecasts are limited to 24 hours and 7 days. Longer "
            "horizons are not supported."
        ),
    ),
    LimitationSpec(
        area="correlation interpretation",
        description=(
            "Correlation does not imply causation; a statistically "
            "significant Pearson coefficient between a macro "
            "indicator and BTC price does not establish that the "
            "indicator drives the price."
        ),
    ),
    LimitationSpec(
        area="regime classification",
        description=(
            "Regime labels are backward-looking: they describe the "
            "price trajectory over a completed window, not a "
            "forward-looking forecast of which regime is next."
        ),
    ),
)


# ============================================================
# CANONICAL INSTANCE
# ============================================================
_METHODOLOGY = Methodology(
    version="1.0.0",
    updated_at="2026-09-16",
    models=list(CANONICAL_MODELS),
    correlations=CANONICAL_CORRELATIONS,
    regimes=CANONICAL_REGIMES,
    data_sources=list(CANONICAL_DATA_SOURCES),
    limitations=list(CANONICAL_LIMITATIONS),
)


def build_methodology() -> Methodology:
    """Return the canonical methodology.

    Today this returns a module-level constant. A4.2 will swap it
    for a lookup against a version registry; call sites go through
    this function so the swap does not require changes anywhere
    else.

    Returns:
        The canonical :class:`Methodology`.
    """
    return _METHODOLOGY


__all__ = [
    "CANONICAL_CORRELATIONS",
    "CANONICAL_DATA_SOURCES",
    "CANONICAL_LIMITATIONS",
    "CANONICAL_MODELS",
    "CANONICAL_REGIMES",
    "CorrelationSpec",
    "DataSourceSpec",
    "LimitationSpec",
    "Methodology",
    "ModelSpec",
    "RegimeSpec",
    "build_methodology",
]