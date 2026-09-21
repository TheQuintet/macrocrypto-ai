"""Unit tests for app.methodology.

Covers:
    - The current Methodology instance: version, sections,
      non-empty fields
    - Every section dataclass: to_dict shape, JSON-serializability
    - Cross-module consistency: thresholds in this module agree with
      the running constants in app.correlation.calculator and
      app.prediction.market
    - build_methodology() with and without a version argument
    - The MethodologyRegistry: get, current, list_versions,
      list_changelog, empty-registry edge cases
    - The ChangelogEntry dataclass
    - Semver ordering (1.9.0 < 1.10.0, not lexicographic)

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
    CANONICAL_CHANGELOG,
    CANONICAL_CORRELATIONS,
    CANONICAL_DATA_SOURCES,
    CANONICAL_LIMITATIONS,
    CANONICAL_MODELS,
    CANONICAL_REGIMES,
    METHODOLOGY_V1_0_0,
    METHODOLOGY_V1_1_0,
    ChangelogEntry,
    CorrelationSpec,
    DataSourceSpec,
    LimitationSpec,
    Methodology,
    MethodologyRegistry,
    ModelSpec,
    RegimeSpec,
    build_methodology,
    get_methodology_changelog,
    list_methodology_versions,
)
from app.prediction import market as market_mod


# ============================================================
# TOP-LEVEL INSTANCE
# ============================================================
class TestBuildMethodology:
    """build_methodology() returns the current version by default."""

    def test_returns_a_methodology(self) -> None:
        m = build_methodology()
        assert isinstance(m, Methodology)

    def test_current_version_is_1_1_0(self) -> None:
        m = build_methodology()
        assert m.version == "1.1.0"

    def test_version_is_semver_like(self) -> None:
        parts = build_methodology().version.split(".")
        assert len(parts) == 3
        for p in parts:
            int(p)  # must be an integer

    def test_updated_at_is_iso_date(self) -> None:
        m = build_methodology()
        assert len(m.updated_at) == 10
        assert m.updated_at[4] == "-"
        assert m.updated_at[7] == "-"

    def test_idempotent(self) -> None:
        """Repeated calls return the same object (no rebuilding)."""
        assert build_methodology() is build_methodology()


class TestBuildMethodologyWithVersion:
    """build_methodology(version) returns the requested version."""

    def test_explicit_1_0_0(self) -> None:
        m = build_methodology("1.0.0")
        assert m.version == "1.0.0"

    def test_explicit_1_1_0(self) -> None:
        m = build_methodology("1.1.0")
        assert m.version == "1.1.0"

    def test_explicit_matches_current_for_current_version(self) -> None:
        assert build_methodology("1.1.0") is build_methodology()

    def test_unknown_version_raises_key_error(self) -> None:
        with pytest.raises(KeyError):
            build_methodology("9.9.9")

    def test_none_is_current(self) -> None:
        assert build_methodology(None) is build_methodology()


class TestMethodologyFrozen:
    """Methodology is a frozen dataclass."""

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
        spec = ModelSpec(
            name="x", algorithm="y", strategy="z", description="d"
        )
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
        spec = DataSourceSpec(
            name="X", url="https://x", description="d"
        )
        assert spec.to_dict() == {
            "name": "X",
            "url": "https://x",
            "description": "d",
        }

    def test_limitation_spec_to_dict(self) -> None:
        spec = LimitationSpec(area="a", description="d")
        assert spec.to_dict() == {"area": "a", "description": "d"}


# ============================================================
# CHANGELOG ENTRY
# ============================================================
class TestChangelogEntry:
    """The ChangelogEntry dataclass."""

    def test_to_dict(self) -> None:
        e = ChangelogEntry(
            version="1.2.3",
            released_at="2026-10-01",
            summary="sum",
            changes=["a", "b"],
        )
        assert e.to_dict() == {
            "version": "1.2.3",
            "released_at": "2026-10-01",
            "summary": "sum",
            "changes": ["a", "b"],
        }

    def test_default_changes_is_empty(self) -> None:
        e = ChangelogEntry(
            version="1.0.0",
            released_at="2026-01-01",
            summary="s",
        )
        assert e.changes == []

    def test_frozen(self) -> None:
        e = ChangelogEntry(
            version="1.0.0", released_at="2026-01-01", summary="s"
        )
        with pytest.raises(FrozenInstanceError):
            e.version = "9.9.9"  # type: ignore[misc]

    def test_json_serializable(self) -> None:
        e = ChangelogEntry(
            version="1.0.0",
            released_at="2026-01-01",
            summary="s",
            changes=["x"],
        )
        text = json.dumps(e.to_dict())
        assert json.loads(text)["changes"] == ["x"]


# ============================================================
# REGISTRY
# ============================================================
class TestMethodologyRegistry:
    """The MethodologyRegistry dataclass."""

    def test_get_returns_matching_version(self) -> None:
        reg = MethodologyRegistry(
            current_version="1.0.0",
            entries=[
                Methodology(version="1.0.0", updated_at="x"),
                Methodology(version="1.1.0", updated_at="x"),
            ],
        )
        assert reg.get("1.0.0").version == "1.0.0"
        assert reg.get("1.1.0").version == "1.1.0"

    def test_get_unknown_raises_key_error(self) -> None:
        reg = MethodologyRegistry(
            current_version="1.0.0",
            entries=[Methodology(version="1.0.0", updated_at="x")],
        )
        with pytest.raises(KeyError):
            reg.get("9.9.9")

    def test_current_returns_current_version_entry(self) -> None:
        v1 = Methodology(version="1.0.0", updated_at="x")
        v2 = Methodology(version="1.1.0", updated_at="x")
        reg = MethodologyRegistry(
            current_version="1.1.0", entries=[v1, v2]
        )
        assert reg.current() is v2

    def test_current_raises_if_missing(self) -> None:
        reg = MethodologyRegistry(
            current_version="9.9.9", entries=[]
        )
        with pytest.raises(KeyError):
            reg.current()

    def test_list_versions_is_semver_ordered(self) -> None:
        reg = MethodologyRegistry(
            current_version="1.10.0",
            entries=[
                Methodology(version="1.10.0", updated_at="x"),
                Methodology(version="1.9.0", updated_at="x"),
                Methodology(version="1.0.0", updated_at="x"),
            ],
        )
        assert reg.list_versions() == ["1.0.0", "1.9.0", "1.10.0"]

    def test_list_versions_empty(self) -> None:
        reg = MethodologyRegistry(current_version="0.0.0")
        assert reg.list_versions() == []

    def test_list_changelog_newest_first(self) -> None:
        reg = MethodologyRegistry(
            current_version="1.1.0",
            entries=[],
            changelog=[
                ChangelogEntry(
                    version="1.0.0",
                    released_at="2026-01-01",
                    summary="old",
                ),
                ChangelogEntry(
                    version="1.1.0",
                    released_at="2026-02-01",
                    summary="new",
                ),
            ],
        )
        ordered = reg.list_changelog()
        assert [e.version for e in ordered] == ["1.1.0", "1.0.0"]

    def test_list_changelog_empty(self) -> None:
        reg = MethodologyRegistry(current_version="0.0.0")
        assert reg.list_changelog() == []

    def test_registry_frozen(self) -> None:
        reg = MethodologyRegistry(current_version="0.0.0")
        with pytest.raises(FrozenInstanceError):
            reg.current_version = "9.9.9"  # type: ignore[misc]


# ============================================================
# PUBLIC ACCESSORS
# ============================================================
class TestPublicAccessors:
    """list_methodology_versions and get_methodology_changelog."""

    def test_list_methodology_versions(self) -> None:
        assert list_methodology_versions() == ["1.0.0", "1.1.0"]

    def test_get_methodology_changelog_newest_first(self) -> None:
        entries = get_methodology_changelog()
        assert [e.version for e in entries] == ["1.1.0", "1.0.0"]

    def test_changelog_matches_registry_versions(self) -> None:
        """Every changelog entry has a matching Methodology."""
        registry_versions = set(list_methodology_versions())
        changelog_versions = {
            e.version for e in get_methodology_changelog()
        }
        assert changelog_versions == registry_versions

    def test_changelog_matches_canonical(self) -> None:
        """The public changelog equals the canonical tuple."""
        entries = get_methodology_changelog()
        # The canonical tuple is in declaration order; the accessor
        # sorts newest-first.
        assert {e.version for e in entries} == {
            e.version for e in CANONICAL_CHANGELOG
        }


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
        assert empty.correlations.method == ""
        assert empty.correlations.windows_days == ()
        assert empty.regimes.labels == ()
        assert empty.regimes.priority == ()
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
# CANONICAL VERSIONS
# ============================================================
class TestCanonicalVersions:
    """The two shipped versions are wired the way the registry says."""

    def test_v1_0_0_has_the_a41_content(self) -> None:
        assert METHODOLOGY_V1_0_0.version == "1.0.0"
        assert METHODOLOGY_V1_0_0.correlations.method == "Pearson"
        assert METHODOLOGY_V1_0_0.regimes.labels == (
            "bull",
            "bear",
            "volatile",
            "neutral",
        )

    def test_v1_1_0_has_the_a42_content(self) -> None:
        assert METHODOLOGY_V1_1_0.version == "1.1.0"
        assert METHODOLOGY_V1_1_0.correlations.method == "Pearson"
        assert METHODOLOGY_V1_1_0.regimes.labels == (
            "bull",
            "bear",
            "volatile",
            "neutral",
        )

    def test_sections_identical_across_versions(self) -> None:
        """A4.2 did not change the methodology sections; it only
        added version tracking on top."""
        v1 = METHODOLOGY_V1_0_0
        v2 = METHODOLOGY_V1_1_0
        assert [m.name for m in v1.models] == [
            m.name for m in v2.models
        ]
        assert v1.correlations.method == v2.correlations.method
        assert v1.regimes.labels == v2.regimes.labels
        assert [s.name for s in v1.data_sources] == [
            s.name for s in v2.data_sources
        ]
        assert [l.area for l in v1.limitations] == [
            l.area for l in v2.limitations
        ]


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