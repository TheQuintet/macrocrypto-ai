"""Unit tests for app.methodology.

Covers:
    - The canonical Methodology instance: version, sections,
      non-empty fields
    - Each section dataclass: to_dict shape, JSON-serializability
    - Cross-module consistency: thresholds in this module agree with
      the running constants in app.correlation.calculator and
      app.prediction.market
    - build_methodology() returns the canonical instance

The cross-module tests are the important ones: they assert that the
methodology documentation and the running code cannot drift apart
without a test failure. If the correlation windows in calculator.py
change, the windows advertised by /api/v1/methodology must change
too — that's what makes this file a source of truth rather than a
copy.

Pure-function tests — no I/O, no mocks, no fixtures beyond the
module under test.
"""

import json
from dataclasses import FrozenInstanceError

import pytest

from app.correlation import calculator as calc
from app.methodology import (
    CANONICAL_CORRELATIONS,
    CANONICAL_DATA_SOURCES,
    CANONICAL_LIMITATIONS,
    CANONICAL_MODELS,
    CANONICAL_REGIMES,
    CorrelationSpec,
    DataSourceSpec,
    LimitationSpec,
    Methodology,
    ModelSpec,
    RegimeSpec,
    build_methodology,
)
from app.prediction import market as market_mod


# ============================================================
# TOP-LEVEL INSTANCE
# ============================================================
class TestBuildMethodology:
    """build_methodology() returns the canonical instance."""

    def test_returns_a_methodology(self) -> None:
        m = build_methodology()
        assert isinstance(m, Methodology)

    def test_version_is_semver_like(self) -> None:
        m = build_methodology()
        parts = m.version.split(".")
        assert len(parts) == 3
        for p in parts:
            int(p)  # must be an integer

    def test_updated_at_is_iso_date(self) -> None:
        m = build_methodology()
        # YYYY-MM-DD
        assert len(m.updated_at) == 10
        assert m.updated_at[4] == "-"
        assert m.updated_at[7] == "-"

    def test_idempotent(self) -> None:
        """Repeated calls return the same object (no rebuilding)."""
        assert build_methodology() is build_methodology()

    def test_frozen(self) -> None:
        m = build_methodology()
        with pytest.raises(FrozenInstanceError):
            m.version = "9.9.9"  # type: ignore[misc]


# ============================================================
# SECTION PRESENCE
# ============================================================
class TestSections:
    """Every section is present and populated."""

    def test_models_present(self) -> None:
        m = build_methodology()
        assert len(m.models) == 6
        names = [x.name for x in m.models]
        assert names == [
            "prophet_fresh",
            "prophet_warm",
            "xgboost_fresh",
            "xgboost_incremental",
            "lightgbm_fresh",
            "lightgbm_incremental",
        ]

    def test_correlations_present(self) -> None:
        m = build_methodology()
        assert m.correlations.method == "Pearson"
        assert m.correlations.windows_days == (30, 90, 365)
        assert m.correlations.indicators == (
            "inflation",
            "rates",
            "gdp",
            "unemployment",
        )

    def test_regimes_present(self) -> None:
        m = build_methodology()
        assert m.regimes.labels == (
            "bull",
            "bear",
            "volatile",
            "neutral",
        )
        assert m.regimes.priority == (
            "volatile",
            "bull",
            "bear",
            "neutral",
        )

    def test_data_sources_present(self) -> None:
        m = build_methodology()
        names = [s.name for s in m.data_sources]
        assert names == ["FRED", "CoinGecko", "MacroCrypto AI Service"]

    def test_limitations_present(self) -> None:
        m = build_methodology()
        assert len(m.limitations) >= 3

    def test_no_empty_descriptions(self) -> None:
        """Every prose field is non-empty."""
        m = build_methodology()
        for model in m.models:
            assert model.description.strip()
            assert model.algorithm.strip()
            assert model.strategy.strip()
        assert m.correlations.description.strip()
        assert m.regimes.description.strip()
        for src in m.data_sources:
            assert src.description.strip()
        for lim in m.limitations:
            assert lim.description.strip()
            assert lim.area.strip()


# ============================================================
# SECTION DATACLASSES
# ============================================================
class TestSectionDataclasses:
    """Each section dataclass's to_dict shape and frozenness."""

    def test_model_spec_to_dict(self) -> None:
        spec = ModelSpec(
            name="x", algorithm="y", strategy="z", description="d"
        )
        assert spec.to_dict() == {
            "name": "x",
            "algorithm": "y",
            "strategy": "z",
            "description": "d",
        }

    def test_model_spec_frozen(self) -> None:
        spec = ModelSpec(name="x", algorithm="y", strategy="z", description="d")
        with pytest.raises(FrozenInstanceError):
            spec.name = "other"  # type: ignore[misc]

    def test_correlation_spec_to_dict_shape(self) -> None:
        spec = CorrelationSpec(
            method="Pearson",
            windows_days=(30, 90),
            strength_thresholds=(0.7, 0.3),
            significance_threshold=0.05,
            indicators=("a", "b"),
            description="d",
        )
        d = spec.to_dict()
        assert d["method"] == "Pearson"
        assert d["windows_days"] == [30, 90]
        assert d["strength_thresholds"] == {
            "strong_gt": 0.7,
            "medium_gte": 0.3,
        }
        assert d["significance_threshold"] == 0.05
        assert d["indicators"] == ["a", "b"]
        assert d["description"] == "d"

    def test_regime_spec_to_dict_shape(self) -> None:
        spec = RegimeSpec(
            labels=("a",),
            priority=("a",),
            bull_threshold_pct=20.0,
            bear_threshold_pct=20.0,
            volatility_threshold=0.05,
            description="d",
        )
        d = spec.to_dict()
        assert d["labels"] == ["a"]
        assert d["priority"] == ["a"]
        assert d["bull_threshold_pct"] == 20.0
        assert d["bear_threshold_pct"] == 20.0
        assert d["volatility_threshold"] == 0.05

    def test_data_source_spec_to_dict(self) -> None:
        spec = DataSourceSpec(name="X", url="https://x", description="d")
        assert spec.to_dict() == {
            "name": "X",
            "url": "https://x",
            "description": "d",
        }

    def test_limitation_spec_to_dict(self) -> None:
        spec = LimitationSpec(area="a", description="d")
        assert spec.to_dict() == {"area": "a", "description": "d"}


# ============================================================
# to_dict ON THE ENVELOPE
# ============================================================
class TestMethodologyToDict:
    """The top-level to_dict produces the full nested structure."""

    def test_shape(self) -> None:
        m = build_methodology()
        d = m.to_dict()
        assert set(d.keys()) == {
            "version",
            "updated_at",
            "models",
            "correlations",
            "regimes",
            "data_sources",
            "limitations",
        }

    def test_nested_lists(self) -> None:
        d = build_methodology().to_dict()
        assert isinstance(d["models"], list)
        assert isinstance(d["data_sources"], list)
        assert isinstance(d["limitations"], list)
        assert isinstance(d["correlations"]["windows_days"], list)
        assert isinstance(d["regimes"]["labels"], list)

    def test_json_serializable(self) -> None:
        payload = build_methodology().to_dict()
        # Should not raise.
        text = json.dumps(payload)
        reloaded = json.loads(text)
        assert reloaded["version"] == build_methodology().version

    def test_default_factory_branches_are_covered(self) -> None:
        """Constructing a Methodology with no sections exercises the
        default_factory lambdas (they are otherwise unreachable)."""
        empty = Methodology(version="0.0.0", updated_at="2026-01-01")
        assert empty.models == []
        assert empty.data_sources == []
        assert empty.limitations == []
        # The section defaults still produce a valid (if empty) spec.
        assert empty.correlations.method == ""
        assert empty.correlations.windows_days == ()
        assert empty.regimes.labels == ()
        assert empty.regimes.priority == ()
        # And to_dict works on the empty instance.
        d = empty.to_dict()
        assert d["correlations"]["windows_days"] == []
        assert d["regimes"]["labels"] == []


# ============================================================
# CROSS-MODULE CONSISTENCY
# ============================================================
class TestCorrelationConsistency:
    """Methodology thresholds match the running calculator."""

    def test_windows_match(self) -> None:
        assert (
            CANONICAL_CORRELATIONS.windows_days == calc.WINDOWS
        )

    def test_strength_thresholds_match(self) -> None:
        strong_gt, medium_gte = (
            CANONICAL_CORRELATIONS.strength_thresholds
        )
        assert strong_gt == calc.STRONG_THRESHOLD
        assert medium_gte == calc.MEDIUM_THRESHOLD

    def test_significance_threshold_matches(self) -> None:
        assert (
            CANONICAL_CORRELATIONS.significance_threshold
            == calc.SIGNIFICANCE_THRESHOLD
        )

    def test_indicators_match_source_columns_keys(self) -> None:
        assert (
            CANONICAL_CORRELATIONS.indicators
            == tuple(calc.INDICATOR_SOURCE_COLUMNS.keys())
        )


class TestRegimeConsistency:
    """Methodology regime labels and thresholds match the classifier."""

    def test_labels_match(self) -> None:
        assert CANONICAL_REGIMES.labels == tuple(
            market_mod.ALL_CONDITIONS
        )

    def test_priority_matches(self) -> None:
        assert CANONICAL_REGIMES.priority == tuple(
            market_mod.CONDITION_PRIORITY
        )


# ============================================================
# IMPORTS ARE THE CANONICAL CONSTANTS
# ============================================================
class TestCanonicalConstantsAreTheImportedOnes:
    """The module-level constants are what the envelope contains."""

    def test_models_match(self) -> None:
        assert tuple(build_methodology().models) == CANONICAL_MODELS

    def test_regimes_match(self) -> None:
        assert build_methodology().regimes is CANONICAL_REGIMES

    def test_correlations_match(self) -> None:
        assert build_methodology().correlations is CANONICAL_CORRELATIONS

    def test_data_sources_match(self) -> None:
        assert (
            tuple(build_methodology().data_sources)
            == CANONICAL_DATA_SOURCES
        )

    def test_limitations_match(self) -> None:
        assert (
            tuple(build_methodology().limitations)
            == CANONICAL_LIMITATIONS
        )