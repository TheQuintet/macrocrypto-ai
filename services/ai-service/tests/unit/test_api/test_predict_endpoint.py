"""Unit tests for the GET /api/v1/predict/btc endpoint.

These tests use FastAPI's TestClient with a mocked repository, so
no live database is required.

Strategy:
    - Override the `get_repository` FastAPI dependency with a fake
      that returns canned data.
    - Assert on status codes, response shape, and computed fields.

Test organization:
    - TestPredictEndpointHappyPath: successful responses
    - TestPredictEndpointEdgeCases: missing data, boundary cases
    - TestPredictEndpointValidation: query-param validation
    - TestPredictEndpointErrors: error responses
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
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
) -> List[PredictionRow]:
    """Build a batch of prediction rows.

    Prices increase linearly from base_price so downstream math is
    predictable in tests.
    """
    base_ts = datetime(2026, 9, 14, 13, 0, tzinfo=timezone.utc)
    prediction_time = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)

    return [
        PredictionRow(
            time=base_ts + timedelta(hours=i),
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