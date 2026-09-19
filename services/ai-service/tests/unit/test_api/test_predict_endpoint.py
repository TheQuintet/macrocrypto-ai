"""Unit tests for the GET /api/v1/predict/btc endpoint.

These tests use FastAPI's TestClient with a mocked repository, so
no live database is required.

Strategy:
    - Override the `get_repository` FastAPI dependency with a fake
      that returns canned data.
    - Patch Redis with the FakeRedis fixture from conftest.py.
    - Assert on status codes, response shape, and computed fields.

Test organization:
    - TestPredictEndpointHappyPath: successful responses
    - TestPredictEndpointEdgeCases: missing data, boundary cases
    - TestPredictEndpointValidation: query-param validation
    - TestPredictEndpointErrors: error responses
    - TestPredictEndpointCaching: cache hit / miss / write behavior
    - TestMultiModelComparison: ?models= multi-model path (M6a)
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
from app.cache.prediction_cache import build_cache_key
from app.database.repositories.prediction_repository import PredictionRow
from app.main import app
from app.schemas import TrendDirection


# ============================================================
# HELPERS
# ============================================================
def _make_rows(
    n: int = 24,
    base_price: float = 50_000.0,
    horizon: str = "24h",
    model_name: str = "prophet",
    confidence: float = 0.85,
    start_hour_offset: int = 0,
) -> List[PredictionRow]:
    """Build a batch of prediction rows.

    Prices increase linearly from base_price so downstream math is
    predictable in tests.
    """
    base_ts = datetime(2026, 9, 14, 13, 0, tzinfo=timezone.utc)
    prediction_time = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)

    return [
        PredictionRow(
            time=base_ts + timedelta(hours=start_hour_offset + i),
            prediction_time=prediction_time,
            horizon=horizon,
            model_name=model_name,
            confidence=confidence,
            predicted_price=base_price + i * 10.0,
            lower_bound=base_price + i * 10.0 - 500.0,
            upper_bound=base_price + i * 10.0 + 500.0,
        )
        for i in range(n)
    ]


def _make_mock_repository(
    rows: Optional[List[PredictionRow]] = None,
    current_price: Optional[float] = 50_000.0,
) -> MagicMock:
    """Build a mock PredictionRepository with async methods."""
    repo = MagicMock()
    repo.fetch_latest_predictions = AsyncMock(return_value=rows or [])
    repo.fetch_latest_close_price = AsyncMock(return_value=current_price)
    return repo


def _make_comparison_repository(
    batches: Optional[Dict[str, List[PredictionRow]]] = None,
    current_price: Optional[float] = 50_000.0,
    best_model: Optional[str] = None,
) -> MagicMock:
    """Build a mock PredictionRepository for the multi-model path.

    The multi-model handler reads `repository.session` to construct
    a PerformanceRepository, so this helper wires up a mock session
    whose `execute()` returns a result whose `.mappings().first()`
    yields the best-model row (or None).

    Args:
        batches: Return value of fetch_latest_predictions_batch().
        current_price: Return value of fetch_latest_close_price().
        best_model: Model name returned by fetch_best_model_by_mae().
            None simulates "no MAE data".
    """
    repo = MagicMock()
    repo.fetch_latest_predictions_batch = AsyncMock(
        return_value=batches or {}
    )
    repo.fetch_latest_close_price = AsyncMock(return_value=current_price)

    # Mock session: PerformanceRepository.fetch_best_model_by_mae
    # calls `await session.execute(stmt)` then `.mappings().first()`.
    if best_model is not None:
        row = {"model_name": best_model, "mean_mae": 100.0}
    else:
        row = None

    result = MagicMock()
    result.mappings.return_value.first.return_value = row

    session = AsyncMock()
    session.execute.return_value = result
    repo.session = session

    return repo


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient with the app's lifespan skipped."""
    return TestClient(app)


def _override_repo(repo: MagicMock):
    """Return a dependency override function for get_repository."""
    async def _dep():
        yield repo
    return _dep


# ============================================================
# HAPPY PATH
# ============================================================
class TestPredictEndpointHappyPath:
    """Successful responses from the endpoint."""

    def test_returns_200(self, client: TestClient) -> None:
        """Test that a valid request returns HTTP 200."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows, current_price=50_000.0)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200

    def test_response_has_expected_keys(self, client: TestClient) -> None:
        """Test that the response includes all expected fields."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        expected_keys = {
            "horizon",
            "model_name",
            "confidence",
            "prediction_time",
            "current_price",
            "predicted_end_price",
            "price_change_pct",
            "trend",
            "predictions",
        }
        assert set(data.keys()) == expected_keys

    def test_response_has_24_predictions(self, client: TestClient) -> None:
        """Test that 24 prediction points are returned for a 24h batch."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        assert len(data["predictions"]) == 24

    def test_predicted_end_price_is_last_row(self, client: TestClient) -> None:
        """Test that predicted_end_price equals the last row's price."""
        rows = _make_rows(24, base_price=50_000.0)
        repo = _make_mock_repository(rows=rows, current_price=50_000.0)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        # Last row: base_price + 23 * 10 = 50_230
        assert data["predicted_end_price"] == 50_230.0

    def test_price_change_pct_computed(self, client: TestClient) -> None:
        """Test that price_change_pct is computed from current to end."""
        rows = _make_rows(24, base_price=50_000.0)
        repo = _make_mock_repository(rows=rows, current_price=50_000.0)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        # (50230 - 50000) / 50000 * 100 = 0.46
        assert data["price_change_pct"] == pytest.approx(0.46, abs=1e-9)

    def test_trend_is_neutral_for_small_change(self, client: TestClient) -> None:
        """Test that +0.46% is NEUTRAL (below 0.5% threshold)."""
        rows = _make_rows(24, base_price=50_000.0)
        repo = _make_mock_repository(rows=rows, current_price=50_000.0)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        assert data["trend"] == TrendDirection.NEUTRAL.value

    def test_trend_is_up_for_large_change(self, client: TestClient) -> None:
        """Test that a large positive change yields trend='up'."""
        rows = _make_rows(24, base_price=50_000.0)
        # Current price much lower than predicted → big positive change
        repo = _make_mock_repository(rows=rows, current_price=40_000.0)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        assert data["trend"] == TrendDirection.UP.value

    def test_trend_is_down_for_large_negative_change(
        self, client: TestClient
    ) -> None:
        """Test that a large negative change yields trend='down'."""
        rows = _make_rows(24, base_price=50_000.0)
        # Current price much higher than predicted → big negative change
        repo = _make_mock_repository(rows=rows, current_price=60_000.0)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        assert data["trend"] == TrendDirection.DOWN.value

    def test_horizon_echoed_in_response(self, client: TestClient) -> None:
        """Test that the requested horizon appears in the response."""
        rows = _make_rows(24, horizon="24h")
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?horizon=24h")
        finally:
            app.dependency_overrides.clear()

        assert response.json()["horizon"] == "24h"

    def test_model_name_echoed_in_response(self, client: TestClient) -> None:
        """Test that the requested model_name appears in the response."""
        rows = _make_rows(24, model_name="prophet")
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?model_name=prophet")
        finally:
            app.dependency_overrides.clear()

        assert response.json()["model_name"] == "prophet"

    def test_7d_horizon_accepted(self, client: TestClient) -> None:
        """Test that horizon=7d is accepted and passed through."""
        rows = _make_rows(7, horizon="7d", base_price=50_000.0)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?horizon=7d")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        assert data["horizon"] == "7d"
        assert len(data["predictions"]) == 7

    def test_confidence_passed_through(self, client: TestClient) -> None:
        """Test that the confidence query param is honored."""
        rows = _make_rows(24, confidence=0.95)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?confidence=0.95")
        finally:
            app.dependency_overrides.clear()

        assert response.json()["confidence"] == 0.95


# ============================================================
# EDGE CASES
# ============================================================
class TestPredictEndpointEdgeCases:
    """Edge-case behavior of the endpoint."""

    def test_null_current_price(self, client: TestClient) -> None:
        """Test that a null current price is handled gracefully."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows, current_price=None)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["current_price"] is None
        assert data["price_change_pct"] is None
        assert data["trend"] == TrendDirection.NEUTRAL.value

    def test_single_prediction(self, client: TestClient) -> None:
        """Test that a single-row batch works (predicted_end = that row)."""
        rows = _make_rows(1, base_price=50_000.0)
        repo = _make_mock_repository(rows=rows, current_price=50_000.0)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 1
        assert data["predicted_end_price"] == 50_000.0

    def test_predictions_ordered_by_time(self, client: TestClient) -> None:
        """Test that prediction points are returned in ascending time order."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        predictions = response.json()["predictions"]
        times = [p["time"] for p in predictions]
        assert times == sorted(times)


# ============================================================
# VALIDATION
# ============================================================
class TestPredictEndpointValidation:
    """Query parameter validation."""

    def test_invalid_horizon_returns_422(self, client: TestClient) -> None:
        """Test that an invalid horizon is rejected with 422."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?horizon=1h")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422

    def test_invalid_confidence_returns_422(self, client: TestClient) -> None:
        """Test that an invalid confidence is rejected with 422."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?confidence=0.5")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422


# ============================================================
# ERROR RESPONSES
# ============================================================
class TestPredictEndpointErrors:
    """Error response behavior."""

    def test_no_predictions_returns_404(self, client: TestClient) -> None:
        """Test that missing predictions yield 404."""
        repo = _make_mock_repository(rows=[])
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404
        data = response.json()
        # FastAPI wraps HTTPException detail in {"detail": ...}
        assert "detail" in data


# ============================================================
# CACHING BEHAVIOR
# ============================================================
class TestPredictEndpointCaching:
    """Cache-aside behavior of the endpoint.

    Uses the FakeRedis fixture from conftest.py, which is autouse
    for everything in tests/unit/test_api/.
    """

    def test_cache_miss_queries_database(
        self, client: TestClient, fake_redis
    ) -> None:
        """Test that on a cold cache, the database is queried."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        repo.fetch_latest_predictions.assert_called_once()
        # Cache was checked (miss) then written
        assert fake_redis.get_calls >= 1
        assert fake_redis.set_calls >= 1

    def test_cache_hit_skips_database(
        self, client: TestClient, fake_redis
    ) -> None:
        """Test that on a warm cache, the database is not queried again."""
        # First call: cold cache → DB → cache populated
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            first = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert first.status_code == 200
        assert repo.fetch_latest_predictions.call_count == 1

        # Second call: repo now returns nothing (simulating a DB miss),
        # but cache should hit so DB is never queried again
        repo.fetch_latest_predictions = AsyncMock(return_value=[])
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            second = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert second.status_code == 200
        # Repo's fetch was NOT called during the second request
        assert repo.fetch_latest_predictions.call_count == 0
        # Second response matches the first
        assert second.json() == first.json()

    def test_cache_key_is_horizon_model_confidence_scoped(
        self, client: TestClient, fake_redis
    ) -> None:
        """Test that different keys produce different cache entries."""
        rows_24h = _make_rows(24, horizon="24h")
        repo = _make_mock_repository(rows=rows_24h)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            client.get("/api/v1/predict/btc?horizon=24h")
            client.get("/api/v1/predict/btc?horizon=24h&confidence=0.95")
        finally:
            app.dependency_overrides.clear()

        expected_24h = build_cache_key("24h", "prophet", 0.85)
        expected_24h_95 = build_cache_key("24h", "prophet", 0.95)
        assert expected_24h in fake_redis._store
        assert expected_24h_95 in fake_redis._store
        assert expected_24h != expected_24h_95

    def test_404_is_not_cached(self, client: TestClient, fake_redis) -> None:
        """Test that 404 responses do not populate the cache."""
        repo = _make_mock_repository(rows=[])
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404
        assert fake_redis.set_calls == 0


# ============================================================
# MULTI-MODEL COMPARISON (M6a)
# ============================================================
class TestMultiModelComparison:
    """Tests for the ?models= multi-model path."""

    def test_missing_models_param_uses_single_model_path(
        self, client: TestClient
    ) -> None:
        """Test that omitting ?models= returns the original shape."""
        rows = _make_rows(24)
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        # Original response shape
        assert "model_name" in data
        assert "predictions" in data
        # No comparison envelope
        assert "comparison" not in data
        assert "models" not in data

    def test_single_model_in_list_uses_single_model_path(
        self, client: TestClient
    ) -> None:
        """Test that ?models=prophet returns the original single-model shape."""
        rows = _make_rows(24, model_name="prophet")
        repo = _make_mock_repository(rows=rows)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?models=prophet")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["model_name"] == "prophet"
        assert "comparison" not in data

    def test_two_models_returns_comparison(
        self, client: TestClient
    ) -> None:
        """Test that ?models=a,b returns a ComparisonResponse envelope."""
        batches = {
            "prophet": _make_rows(3, model_name="prophet"),
            "xgboost_fresh": _make_rows(
                3, model_name="xgboost_fresh"
            ),
        }
        repo = _make_comparison_repository(
            batches=batches, best_model="prophet"
        )
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get(
                "/api/v1/predict/btc?models=prophet,xgboost_fresh"
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "comparison" in data
        assert set(data["models"].keys()) == {"prophet", "xgboost_fresh"}
        assert data["comparison"]["best_model"] == "prophet"

    def test_comparison_has_consensus(
        self, client: TestClient
    ) -> None:
        """Test that consensus is populated for 2+ overlapping models."""
        batches = {
            "a": _make_rows(3, model_name="a"),
            "b": _make_rows(3, model_name="b"),
        }
        repo = _make_comparison_repository(batches=batches)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?models=a,b")
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        assert data["comparison"]["timestamps_compared"] == 3
        assert data["comparison"]["models_compared"] == ["a", "b"]
        assert len(data["comparison"]["models_missing"]) == 0

    def test_agreement_score_is_one_for_identical_models(
        self, client: TestClient
    ) -> None:
        """Test that identical predictions yield agreement 1.0."""
        batches = {
            "a": _make_rows(3, model_name="a"),
            "b": _make_rows(3, model_name="b"),
        }
        repo = _make_comparison_repository(batches=batches)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?models=a,b")
        finally:
            app.dependency_overrides.clear()

        assert response.json()["comparison"]["agreement_score"] == 1.0

    def test_unknown_model_lands_in_missing(
        self, client: TestClient
    ) -> None:
        """Test that an unknown model name appears in missing_models."""
        batches = {
            "prophet": _make_rows(3, model_name="prophet"),
        }
        repo = _make_comparison_repository(batches=batches)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get(
                "/api/v1/predict/btc?models=prophet,ghost"
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "ghost" in data["missing_models"]
        assert "ghost" in data["comparison"]["models_missing"]

    def test_empty_models_param_returns_422(
        self, client: TestClient
    ) -> None:
        """Test that ?models= (empty) returns 422."""
        repo = _make_comparison_repository()
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get("/api/v1/predict/btc?models=")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422

    def test_empty_segment_returns_422(self, client: TestClient) -> None:
        """Test that a doubled comma returns 422."""
        repo = _make_comparison_repository()
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get(
                "/api/v1/predict/btc?models=a,,b"
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422

    def test_duplicate_model_returns_422(self, client: TestClient) -> None:
        """Test that duplicate model names return 422."""
        repo = _make_comparison_repository()
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get(
                "/api/v1/predict/btc?models=prophet,prophet"
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422

    def test_no_batches_returns_404(self, client: TestClient) -> None:
        """Test that an empty batch dict yields 404."""
        repo = _make_comparison_repository(batches={})
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            response = client.get(
                "/api/v1/predict/btc?models=prophet,xgboost_fresh"
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_comparison_cached(
        self, client: TestClient, fake_redis
    ) -> None:
        """Test that the multi-model response is cached under one key."""
        batches = {
            "a": _make_rows(3, model_name="a"),
            "b": _make_rows(3, model_name="b"),
        }
        repo = _make_comparison_repository(batches=batches)
        app.dependency_overrides[get_repository] = _override_repo(repo)

        try:
            first = client.get("/api/v1/predict/btc?models=a,b")
            # Second call with same models in different order — should
            # hit the same cache key (sorted internally).
            second = client.get("/api/v1/predict/btc?models=b,a")
        finally:
            app.dependency_overrides.clear()

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json() == first.json()
        # Repo only hit once (second call came from cache)
        assert repo.fetch_latest_predictions_batch.call_count == 1