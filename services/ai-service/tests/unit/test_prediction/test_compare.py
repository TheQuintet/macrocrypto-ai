"""Unit tests for app.prediction.compare.

Pure-function tests — no DB, no FastAPI, no mocks. Covers:
    - ConsensusPoint dataclass
    - StoredComparison dataclass
    - compare_stored_predictions() across single-model, multi-model,
      missing, non-overlapping, and empty-input cases
    - _agreement_from_yhats() math
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List

import pytest

from app.database.repositories.prediction_repository import PredictionRow
from app.prediction.compare import (
    AGREEMENT_SCORE_MAX,
    AGREEMENT_SCORE_MIN,
    ConsensusPoint,
    StoredComparison,
    _agreement_from_yhats,
    compare_stored_predictions,
)


# ============================================================
# HELPERS
# ============================================================
def _make_rows(
    prices: List[float],
    model_name: str = "prophet",
    start_hour: int = 0,
) -> List[PredictionRow]:
    """Build rows at hourly intervals with the given prices."""
    base_ts = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
    prediction_time = datetime(2026, 9, 14, 11, 0, tzinfo=timezone.utc)
    return [
        PredictionRow(
            time=base_ts + timedelta(hours=start_hour + i),
            prediction_time=prediction_time,
            horizon="24h",
            model_name=model_name,
            confidence=0.85,
            predicted_price=p,
            lower_bound=p - 500.0,
            upper_bound=p + 500.0,
        )
        for i, p in enumerate(prices)
    ]


# ============================================================
# ConsensusPoint
# ============================================================
class TestConsensusPoint:
    """Tests for the ConsensusPoint dataclass."""

    def test_construction(self) -> None:
        """Test construction with all fields."""
        ts = datetime.now(timezone.utc)
        point = ConsensusPoint(
            time=ts,
            predicted_price=50_000.0,
            lower_bound=49_500.0,
            upper_bound=50_500.0,
            contributing_models=3,
        )
        assert point.time == ts
        assert point.predicted_price == 50_000.0
        assert point.contributing_models == 3

    def test_to_dict_keys(self) -> None:
        """Test to_dict returns the expected keys."""
        point = ConsensusPoint(
            time=datetime.now(timezone.utc),
            predicted_price=50_000.0,
        )
        d = point.to_dict()
        assert set(d.keys()) == {
            "time",
            "predicted_price",
            "lower_bound",
            "upper_bound",
            "contributing_models",
        }

    def test_repr_contains_metric(self) -> None:
        """Test __repr__ mentions the price and model count."""
        point = ConsensusPoint(
            time=datetime.now(timezone.utc),
            predicted_price=50_000.0,
            contributing_models=2,
        )
        r = repr(point)
        assert "ConsensusPoint" in r
        assert "50000" in r or "50,000" in r or "50000.00" in r

    def test_optional_bounds(self) -> None:
        """Test that bounds may be None."""
        point = ConsensusPoint(
            time=datetime.now(timezone.utc),
            predicted_price=50_000.0,
            lower_bound=None,
            upper_bound=None,
        )
        assert point.lower_bound is None
        assert point.upper_bound is None


# ============================================================
# StoredComparison
# ============================================================
class TestStoredComparison:
    """Tests for the StoredComparison dataclass."""

    def test_defaults(self) -> None:
        """Test the default-constructed value."""
        result = StoredComparison()
        assert result.models_compared == []
        assert result.models_missing == []
        assert result.consensus == []
        assert result.agreement_score == 0.0
        assert result.best_model is None
        assert result.timestamps_compared == 0

    def test_to_dict_keys(self) -> None:
        """Test to_dict returns the expected keys."""
        result = StoredComparison()
        d = result.to_dict()
        assert set(d.keys()) == {
            "models_compared",
            "models_missing",
            "consensus",
            "agreement_score",
            "best_model",
            "timestamps_compared",
        }

    def test_to_dict_serializes_consensus(self) -> None:
        """Test consensus points are serialized as dicts."""
        result = StoredComparison(
            consensus=[
                ConsensusPoint(
                    time=datetime(2026, 9, 14, tzinfo=timezone.utc),
                    predicted_price=50_000.0,
                )
            ],
        )
        d = result.to_dict()
        assert isinstance(d["consensus"][0], dict)
        assert d["consensus"][0]["predicted_price"] == 50_000.0

    def test_repr_returns_string(self) -> None:
        """Test __repr__ returns a string."""
        assert isinstance(repr(StoredComparison()), str)


# ============================================================
# compare_stored_predictions
# ============================================================
class TestCompareStoredPredictions:
    """Tests for compare_stored_predictions()."""

    def test_empty_batches(self) -> None:
        """Test empty input produces an empty result."""
        result = compare_stored_predictions({})
        assert result.models_compared == []
        assert result.models_missing == []
        assert result.consensus == []
        assert result.agreement_score == 0.0
        assert result.timestamps_compared == 0

    def test_single_model_trivial_agreement(self) -> None:
        """Test a single model yields agreement 1.0 and no consensus.

        With only one model, there is no pair of timestamps to
        compare, so consensus is empty and agreement defaults to
        1.0 (single-model degenerate case).
        """
        batches = {"prophet": _make_rows([50_000.0, 50_100.0])}
        result = compare_stored_predictions(batches)
        assert result.models_compared == []
        assert result.models_missing == ["prophet"]
        assert result.consensus == []
        assert result.agreement_score == 0.0

    def test_two_models_identical(self) -> None:
        """Test two models with identical predictions agree perfectly."""
        batches = {
            "prophet": _make_rows([50_000.0, 50_100.0, 50_200.0]),
            "xgboost_fresh": _make_rows(
                [50_000.0, 50_100.0, 50_200.0], model_name="xgboost_fresh"
            ),
        }
        result = compare_stored_predictions(batches)
        assert set(result.models_compared) == {"prophet", "xgboost_fresh"}
        assert result.models_missing == []
        assert result.timestamps_compared == 3
        assert result.agreement_score == pytest.approx(1.0)

    def test_two_models_slightly_different(self) -> None:
        """Test two models with small divergence agree highly."""
        batches = {
            "prophet": _make_rows([50_000.0, 50_100.0, 50_200.0]),
            "xgboost_fresh": _make_rows(
                [50_010.0, 50_090.0, 50_210.0], model_name="xgboost_fresh"
            ),
        }
        result = compare_stored_predictions(batches)
        # Small spread relative to mean → agreement near 1.0
        assert 0.99 < result.agreement_score <= 1.0

    def test_two_models_wildly_different(self) -> None:
        """Test wildly different predictions yield low agreement."""
        batches = {
            "prophet": _make_rows([50_000.0, 50_100.0, 50_200.0]),
            "xgboost_fresh": _make_rows(
                [10_000.0, 10_100.0, 10_200.0], model_name="xgboost_fresh"
            ),
        }
        result = compare_stored_predictions(batches)
        # Spread ≈ mean → agreement clamped near 0
        assert result.agreement_score < 0.1

    def test_consensus_is_mean_of_models(self) -> None:
        """Test the consensus price is the arithmetic mean."""
        batches = {
            "a": _make_rows([100.0, 200.0]),
            "b": _make_rows([300.0, 400.0], model_name="b"),
        }
        result = compare_stored_predictions(batches)
        prices = [p.predicted_price for p in result.consensus]
        assert prices == [200.0, 300.0]

    def test_consensus_contributing_count(self) -> None:
        """Test contributing_models counts only overlapping models."""
        batches = {
            "a": _make_rows([100.0, 200.0]),
            "b": _make_rows([300.0, 400.0], model_name="b"),
            "c": _make_rows([500.0, 600.0], model_name="c"),
        }
        result = compare_stored_predictions(batches)
        assert all(p.contributing_models == 3 for p in result.consensus)

    def test_missing_model_listed(self) -> None:
        """Test an empty batch is listed in models_missing."""
        batches = {
            "prophet": _make_rows([100.0, 200.0]),
            "ghost": [],
        }
        result = compare_stored_predictions(batches)
        assert "ghost" in result.models_missing
        assert "prophet" in result.models_missing  # no overlap either

    def test_no_overlap_models_are_missing(self) -> None:
        """Test models with non-overlapping timestamps are missing.

        If two models' timestamps never coincide, neither contributes
        to any consensus point, so both go into models_missing.
        """
        batches = {
            "a": _make_rows([100.0, 200.0], start_hour=0),
            "b": _make_rows([300.0, 400.0], model_name="b", start_hour=10),
        }
        result = compare_stored_predictions(batches)
        assert result.models_compared == []
        assert set(result.models_missing) == {"a", "b"}

    def test_best_model_passthrough(self) -> None:
        """Test the best_model argument is passed through unchanged."""
        batches = {
            "a": _make_rows([100.0]),
            "b": _make_rows([200.0], model_name="b"),
        }
        result = compare_stored_predictions(
            batches, best_model="lightgbm_fresh"
        )
        assert result.best_model == "lightgbm_fresh"

    def test_consensus_is_sorted_by_time(self) -> None:
        """Test consensus points are ordered ascending by time."""
        batches = {
            "a": _make_rows([100.0, 200.0, 300.0]),
            "b": _make_rows([100.0, 200.0, 300.0], model_name="b"),
        }
        result = compare_stored_predictions(batches)
        times = [p.time for p in result.consensus]
        assert times == sorted(times)

    def test_requested_models_reported_missing(self) -> None:
        """Test that a requested model absent from batches is reported.

        fetch_latest_predictions_batch omits models with no stored
        rows, so compare_stored_predictions needs the caller's
        requested list to correctly populate models_missing.
        """
        batches = {
            "prophet": _make_rows([100.0, 200.0]),
        }
        result = compare_stored_predictions(
            batches,
            requested_models=["prophet", "ghost"],
        )
        assert "ghost" in result.models_missing
        assert "prophet" in result.models_missing  # no overlap either

    def test_requested_models_defaults_to_batch_keys(self) -> None:
        """Test that omitting requested_models falls back to batch keys."""
        batches = {
            "a": _make_rows([100.0]),
            "b": _make_rows([200.0], model_name="b"),
        }
        result = compare_stored_predictions(batches)
        # With no explicit requested list, only batch keys are considered
        assert set(result.models_missing) == set()


# ============================================================
# _agreement_from_yhats
# ============================================================
class TestAgreementFromYhats:
    """Tests for the internal agreement helper."""

    def test_empty_input_returns_one(self) -> None:
        """Test no timestamps → agreement 1.0."""
        assert _agreement_from_yhats([]) == 1.0

    def test_identical_values_returns_one(self) -> None:
        """Test identical values per timestamp → agreement 1.0."""
        assert _agreement_from_yhats([[100.0, 100.0]]) == pytest.approx(1.0)

    def test_zero_mean_is_skipped(self) -> None:
        """Test timestamps with mean 0 are skipped."""
        # Only one valid timestamp contributes, and it's identical
        assert _agreement_from_yhats([[0.0, 0.0], [100.0, 100.0]]) == 1.0

    def test_clamped_high(self) -> None:
        """Test agreement never exceeds 1.0."""
        result = _agreement_from_yhats([[100.0, 100.0]])
        assert result <= AGREEMENT_SCORE_MAX

    def test_clamped_low(self) -> None:
        """Test agreement never drops below 0.0."""
        result = _agreement_from_yhats([[100.0, 0.001]])
        assert result >= AGREEMENT_SCORE_MIN