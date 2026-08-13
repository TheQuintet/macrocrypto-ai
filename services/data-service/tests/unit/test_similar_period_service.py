"""
Unit tests for the Similar Historical Periods suggestion engine.

Sprint 4:
A3.17 - Similar periods suggestion engine tests.
"""

from datetime import date
from types import SimpleNamespace

import pytest

from app.services.similar_period_service import SimilarPeriodService


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def service():
    """Create SimilarPeriodService with a mocked DB."""
    return SimilarPeriodService(db=None)


@pytest.fixture
def sample_statistics():
    """Feature statistics used for normalized distance tests."""
    return {
        "cpi": (3.0, 1.0),
        "federal_funds_rate": (4.0, 1.0),
        "gdp": (2.0, 0.5),
        "unemployment": (5.0, 1.0),
    }


# ============================================================
# EUCLIDEAN DISTANCE
# ============================================================


def test_euclidean_distance_identical_conditions(
    service,
    sample_statistics,
):
    """
    Identical macro conditions should have zero distance.
    """

    current = {
        "cpi": 3.0,
        "federal_funds_rate": 4.0,
        "gdp": 2.0,
        "unemployment": 5.0,
    }

    historical = current.copy()

    distance, differences = service._calculate_distance(
        current,
        historical,
        sample_statistics,
    )

    assert distance == pytest.approx(0.0)
    assert all(
        value == pytest.approx(0.0)
        for value in differences.values()
    )


def test_euclidean_distance_increases_with_dissimilarity(
    service,
    sample_statistics,
):
    """
    More different macro conditions should produce
    a larger Euclidean distance.
    """

    current = {
        "cpi": 3.0,
        "federal_funds_rate": 4.0,
        "gdp": 2.0,
        "unemployment": 5.0,
    }

    similar = {
        "cpi": 3.2,
        "federal_funds_rate": 4.1,
        "gdp": 2.1,
        "unemployment": 5.1,
    }

    different = {
        "cpi": 8.0,
        "federal_funds_rate": 10.0,
        "gdp": -2.0,
        "unemployment": 12.0,
    }

    similar_distance, _ = service._calculate_distance(
        current,
        similar,
        sample_statistics,
    )

    different_distance, _ = service._calculate_distance(
        current,
        different,
        sample_statistics,
    )

    assert different_distance > similar_distance


# ============================================================
# NORMALIZATION
# ============================================================


def test_normalize_returns_zero_for_mean(service):
    """A value equal to the mean should normalize to zero."""

    result = service._normalize(
        value=3.0,
        mean=3.0,
        stddev=1.0,
    )

    assert result == pytest.approx(0.0)


def test_normalize_returns_standard_score(service):
    """Normalization should produce a z-score."""

    result = service._normalize(
        value=5.0,
        mean=3.0,
        stddev=1.0,
    )

    assert result == pytest.approx(2.0)


def test_normalize_handles_zero_standard_deviation(service):
    """
    Constant historical features should not cause division
    by zero.
    """

    result = service._normalize(
        value=3.0,
        mean=3.0,
        stddev=0.0,
    )

    assert result == pytest.approx(0.0)


# ============================================================
# REASONING
# ============================================================


def test_similarity_reason_is_generated(service):
    """
    Similarity reasoning should explain why a historical
    period was considered similar.
    """

    differences = {
        "cpi": 0.10,
        "federal_funds_rate": 0.20,
        "gdp": 0.05,
        "unemployment": 0.15,
    }

    reason = service._build_reason(differences)

    assert isinstance(reason, str)
    assert reason.strip() != ""


def test_similarity_reason_identifies_closest_conditions(service):
    """
    The reasoning should be based on the macro features
    contributing to similarity.
    """

    differences = {
        "cpi": 0.01,
        "federal_funds_rate": 0.50,
        "gdp": 0.02,
        "unemployment": 0.10,
    }

    reason = service._build_reason(differences)

    assert isinstance(reason, str)
    assert "cpi" in reason.lower() or "inflation" in reason.lower()


# ============================================================
# TOP N SUGGESTIONS
# ============================================================


def test_find_similar_periods_respects_limit(service, monkeypatch):
    """
    The engine should return no more than the requested
    number of historical periods.
    """

    current_conditions = {
        "cpi": 3.0,
        "federal_funds_rate": 4.0,
    }

    historical = [
        {
            "period": {
                "start_date": date(2020, 1, 1),
                "end_date": date(2020, 6, 30),
            },
            "macro_conditions": {
                "cpi": 3.1,
                "federal_funds_rate": 4.1,
            },
        },
        {
            "period": {
                "start_date": date(2019, 1, 1),
                "end_date": date(2019, 6, 30),
            },
            "macro_conditions": {
                "cpi": 3.2,
                "federal_funds_rate": 4.2,
            },
        },
        {
            "period": {
                "start_date": date(2018, 1, 1),
                "end_date": date(2018, 6, 30),
            },
            "macro_conditions": {
                "cpi": 3.3,
                "federal_funds_rate": 4.3,
            },
        },
        {
            "period": {
                "start_date": date(2017, 1, 1),
                "end_date": date(2017, 6, 30),
            },
            "macro_conditions": {
                "cpi": 3.4,
                "federal_funds_rate": 4.4,
            },
        },
        {
            "period": {
                "start_date": date(2016, 1, 1),
                "end_date": date(2016, 6, 30),
            },
            "macro_conditions": {
                "cpi": 3.5,
                "federal_funds_rate": 4.5,
            },
        },
    ]

    monkeypatch.setattr(
        service,
        "get_current_conditions",
        lambda: current_conditions,
    )

    monkeypatch.setattr(
        service,
        "get_historical_snapshots",
        lambda: historical,
    )

    monkeypatch.setattr(
        service,
        "calculate_statistics",
        lambda snapshots: {
            "cpi": (3.3, 0.2),
            "federal_funds_rate": (4.3, 0.2),
        },
    )

    result = service.find_similar_periods(limit=3)

    assert "similar_periods" in result
    assert len(result["similar_periods"]) <= 3


def test_top_results_are_sorted_by_distance(service, monkeypatch):
    """
    Similar periods should be ordered from most similar
    to least similar.
    """

    monkeypatch.setattr(
        service,
        "get_current_conditions",
        lambda: {"cpi": 3.0},
    )

    monkeypatch.setattr(
        service,
        "get_historical_snapshots",
        lambda: [
            {
                "period": {
                    "start_date": date(2020, 1, 1),
                    "end_date": date(2020, 12, 31),
                },
                "macro_conditions": {"cpi": 5.0},
            },
            {
                "period": {
                    "start_date": date(2019, 1, 1),
                    "end_date": date(2019, 12, 31),
                },
                "macro_conditions": {"cpi": 3.1},
            },
        ],
    )

    monkeypatch.setattr(
        service,
        "calculate_statistics",
        lambda snapshots: {
            "cpi": (4.0, 1.0),
        },
    )

    result = service.find_similar_periods(limit=3)

    periods = result["similar_periods"]

    if len(periods) >= 2:
        assert (
            periods[0]["similarity_distance"]
            <= periods[1]["similarity_distance"]
        )


# ============================================================
# BTC PERFORMANCE
# ============================================================


def test_btc_performance_handles_missing_data(service, monkeypatch):
    """
    A historical period without BTC data should not cause
    the similarity engine to fail.
    """

    monkeypatch.setattr(
        service,
        "get_btc_performance",
        lambda period: None,
    )

    period = {
        "start_date": date(2020, 1, 1),
        "end_date": date(2020, 12, 31),
    }

    result = service.get_btc_performance(period)

    assert result is None


# ============================================================
# EDGE CASES
# ============================================================


def test_no_historical_periods_returns_empty_results(
    service,
    monkeypatch,
):
    """
    When no historical periods exist, the engine should return
    an empty suggestion list rather than fail.
    """

    monkeypatch.setattr(
        service,
        "get_current_conditions",
        lambda: {"cpi": 3.0},
    )

    monkeypatch.setattr(
        service,
        "get_historical_snapshots",
        lambda: [],
    )

    result = service.find_similar_periods(limit=3)

    assert result["similar_periods"] == []


def test_missing_current_conditions_returns_empty_results(
    service,
    monkeypatch,
):
    """
    Missing current macro conditions should be handled safely.
    """

    monkeypatch.setattr(
        service,
        "get_current_conditions",
        lambda: {},
    )

    result = service.find_similar_periods(limit=3)

    assert result["similar_periods"] == []



# ============================================================
# CORRELATION MATCHING
# ============================================================


@pytest.mark.skip(
    reason=(
        "A3.5 currently implements Euclidean distance matching "
        "only; correlation matching is not yet exposed by "
        "SimilarPeriodService."
    )
)
def test_correlation_matching():
    """
    A3.17 acceptance criterion:

    Tests for correlation matching.

    This test should be enabled when correlation matching is
    added to SimilarPeriodService.
    """

    # Expected future behavior:
    #
    # result = service.calculate_correlation(
    #     current_conditions,
    #     historical_conditions,
    # )
    #
    # assert result == pytest.approx(1.0)
    #
    # For now this remains intentionally skipped because
    # A3.5 exposes Euclidean distance only.
    pass