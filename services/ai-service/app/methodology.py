"""Methodology documentation for the AI Service (A4.1, A4.2).

This module is the canonical, machine-readable description of how
the AI Service produces its predictions, correlations, and regime
labels. It exists so the methodology can be served via the API
(A4.1) and so its version history is tracked in code (A4.2).

Design:

    - Pure data. Every section is a frozen dataclass. The module
      has no I/O, no dependencies on settings, and no imports from
      the rest of the app.
    - Values are the source of truth. Every threshold, window,
      label, and identifier in here mirrors a constant that the
      running code uses — ``WINDOWS`` and ``SIGNIFICANCE_THRESHOLD``
      in ``app.correlation.calculator``, the regime labels in
      ``app.prediction.market``, the data sources in
      ``app.export.metadata``. The tests in
      ``tests/unit/test_methodology.py`` assert that the two agree,
      so drift fails loudly.
    - Version tracking (A4.2). The module holds a registry of every
      ``Methodology`` version ever shipped, plus a parallel changelog
      of one ``ChangelogEntry`` per version. ``build_methodology()``
      returns the current version by default, and any prior version
      when called with an explicit version string.
    - The ``to_dict`` methods produce JSON-serializable output.
      Nested dataclasses are converted recursively.

Versioning rules:

    - The version string is semver (``MAJOR.MINOR.PATCH``).
    - Every new methodology release gets a new ``Methodology``
      instance, a new ``ChangelogEntry``, and a bump to
      ``current_version`` in the registry.
    - The changelog is append-only. Editing an existing entry after
      the fact would hide the historical record; if a mistake is
      found, add a new version that corrects it.
    - Prior versions are preserved exactly as they were shipped, so
      ``GET /api/v1/methodology?version=1.0.0`` returns what the
      API returned before A4.2.

Not in this module:

    - The response envelope (``MethodologyResponse``) — that lives
      in ``app.schemas.methodology``.
    - The endpoint itself — that lives in
      ``app.api.v1.methodology``.
    - Version comparison logic — deferred; the ticket marks it
      optional.
"""

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

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
    """The full methodology documentation for one version.

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
# CHANGELOG
# ============================================================
@dataclass(frozen=True)
class ChangelogEntry:
    """One entry in the methodology changelog.

    Attributes:
        version: The methodology version this entry describes. Every
            entry must correspond to a ``Methodology`` instance in
            the registry.
        released_at: ISO 8601 date the version was released.
        summary: One-sentence description of what changed.
        changes: A list of short bullet-style strings describing the
            individual changes in this version.
    """

    version: str
    released_at: str
    summary: str
    changes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dict."""
        return {
            "version": self.version,
            "released_at": self.released_at,
            "summary": self.summary,
            "changes": list(self.changes),
        }


# ============================================================
# REGISTRY
# ============================================================
@dataclass(frozen=True)
class MethodologyRegistry:
    """Holds every methodology version plus the changelog.

    The registry is the single source of truth for version lookup.
    ``current_version`` names the version returned by
    ``build_methodology()`` when the caller does not ask for a
    specific one.

    Attributes:
        current_version: The version treated as "current".
        entries: Every ``Methodology`` ever shipped, in no
            particular order. Lookup is by ``version`` field.
        changelog: Every ``ChangelogEntry``, in no particular order.
            ``list_changelog()`` returns them newest-first.
    """

    current_version: str
    entries: List[Methodology] = field(default_factory=list)
    changelog: List[ChangelogEntry] = field(default_factory=list)

    def get(self, version: str) -> Methodology:
        """Return the ``Methodology`` for ``version``.

        Args:
            version: A semver string present in the registry.

        Returns:
            The matching :class:`Methodology`.

        Raises:
            KeyError: If ``version`` is not in the registry. The
                caller is expected to translate this into a 404.
        """
        for entry in self.entries:
            if entry.version == version:
                return entry
        raise KeyError(version)

    def current(self) -> Methodology:
        """Return the current ``Methodology``.

        Raises:
            KeyError: If ``current_version`` does not appear in
                ``entries``. That would be a bug — a release must
                register both.
        """
        return self.get(self.current_version)

    def list_versions(self) -> List[str]:
        """Return every registered version in ascending order.

        Sort is by semver tuple so ``1.10.0`` sorts after ``1.9.0``,
        not before it as a lexicographic sort would produce.

        Returns:
            A new list of version strings.
        """
        return sorted(
            (e.version for e in self.entries),
            key=_semver_key,
        )

    def list_changelog(self) -> List[ChangelogEntry]:
        """Return the changelog, newest version first.

        Returns:
            A new list of :class:`ChangelogEntry` instances.
        """
        return sorted(
            self.changelog,
            key=lambda e: _semver_key(e.version),
            reverse=True,
        )


# ============================================================
# SEMVER HELPER
# ============================================================
def _semver_key(version: str) -> Tuple[int, int, int]:
    """Convert a semver string to a sortable tuple.

    The registry's versions are all three-part (MAJOR.MINOR.PATCH)
    with integer components, so a simple tuple is enough. Non-
    integer or differently-shaped strings would raise ``ValueError``
    at import time, which is the failure mode we want: a malformed
    version is a bug in the module, not a runtime condition.

    Args:
        version: A semver string.

    Returns:
        A ``(major, minor, patch)`` tuple.
    """
    parts = version.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


# ============================================================
# CANONICAL CONTENT — SHARED SECTIONS
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
# VERSION 1.0.0 — A4.1 RELEASE
# ============================================================
# The pre-A4.2 methodology, preserved exactly as it was served by
# the A4.1 endpoint. Do not edit this instance; add a new version
# instead.
METHODOLOGY_V1_0_0 = Methodology(
    version="1.0.0",
    updated_at="2026-09-16",
    models=list(CANONICAL_MODELS),
    correlations=CANONICAL_CORRELATIONS,
    regimes=CANONICAL_REGIMES,
    data_sources=list(CANONICAL_DATA_SOURCES),
    limitations=list(CANONICAL_LIMITATIONS),
)


# ============================================================
# VERSION 1.1.0 — A4.2 RELEASE (CURRENT)
# ============================================================
# The A4.2 release. The methodology content itself is unchanged
# from 1.0.0; the version bump documents the addition of version
# tracking and the changelog as part of the API contract.
METHODOLOGY_V1_1_0 = Methodology(
    version="1.1.0",
    updated_at="2026-09-16",
    models=list(CANONICAL_MODELS),
    correlations=CANONICAL_CORRELATIONS,
    regimes=CANONICAL_REGIMES,
    data_sources=list(CANONICAL_DATA_SOURCES),
    limitations=list(CANONICAL_LIMITATIONS),
)


# ============================================================
# CHANGELOG
# ============================================================
# Append-only. Add a new entry when shipping a new version; do not
# edit existing entries.
CANONICAL_CHANGELOG: Tuple[ChangelogEntry, ...] = (
    ChangelogEntry(
        version="1.0.0",
        released_at="2026-09-16",
        summary=(
            "Initial published methodology: model variants, "
            "correlation method, regime classification, data "
            "sources, and known limitations."
        ),
        changes=[
            "Documented the six forecasting model variants.",
            "Documented the Pearson correlation method with "
            "30/90/365-day windows and 0.7/0.3/0.05 thresholds.",
            "Documented the four regime labels and their priority "
            "order.",
            "Listed the three external data sources (FRED, "
            "CoinGecko, AI Service).",
            "Listed four known limitations.",
        ],
    ),
    ChangelogEntry(
        version="1.1.0",
        released_at="2026-09-16",
        summary=(
            "Added version tracking and a changelog to the "
            "methodology API. Methodology content unchanged from "
            "1.0.0."
        ),
        changes=[
            "The methodology API now reports its version and "
            "exposes a version history.",
            "A changelog endpoint lists every released version.",
            "GET /api/v1/methodology accepts an optional ?version= "
            "query parameter; omitting it returns the current "
            "version, matching the pre-1.1.0 behavior.",
        ],
    ),
)


# ============================================================
# REGISTRY INSTANCE
# ============================================================
_REGISTRY = MethodologyRegistry(
    current_version="1.1.0",
    entries=[METHODOLOGY_V1_0_0, METHODOLOGY_V1_1_0],
    changelog=list(CANONICAL_CHANGELOG),
)


# ============================================================
# PUBLIC ACCESSORS
# ============================================================
def build_methodology(version: Optional[str] = None) -> Methodology:
    """Return the methodology for a given version, or the current one.

    Args:
        version: A registered version string, or ``None`` to
            return the current version. Passing ``None`` matches
            the pre-A4.2 behavior of this function, so existing
            call sites do not need to change.

    Returns:
        The requested :class:`Methodology`, or the current one when
        ``version`` is ``None``.

    Raises:
        KeyError: If ``version`` is provided and not present in the
            registry. Callers should translate this into a 404.
    """
    if version is None:
        return _REGISTRY.current()
    return _REGISTRY.get(version)


def list_methodology_versions() -> List[str]:
    """Return every registered methodology version, ascending.

    Returns:
        A new list of version strings, oldest first.
    """
    return _REGISTRY.list_versions()


def get_methodology_changelog() -> List[ChangelogEntry]:
    """Return the methodology changelog, newest version first.

    Returns:
        A new list of :class:`ChangelogEntry` instances.
    """
    return _REGISTRY.list_changelog()


__all__ = [
    "CANONICAL_CHANGELOG",
    "CANONICAL_CORRELATIONS",
    "CANONICAL_DATA_SOURCES",
    "CANONICAL_LIMITATIONS",
    "CANONICAL_MODELS",
    "CANONICAL_REGIMES",
    "ChangelogEntry",
    "CorrelationSpec",
    "DataSourceSpec",
    "LimitationSpec",
    "METHODOLOGY_V1_0_0",
    "METHODOLOGY_V1_1_0",
    "Methodology",
    "MethodologyRegistry",
    "ModelSpec",
    "RegimeSpec",
    "build_methodology",
    "get_methodology_changelog",
    "list_methodology_versions",
]