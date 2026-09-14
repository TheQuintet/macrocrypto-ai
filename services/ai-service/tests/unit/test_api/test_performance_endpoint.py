"""Unit tests for the GET /api/v1/performance/btc endpoint.

These tests use FastAPI's TestClient with a mocked repository and
a mocked threshold repository, so no live database is required.

Strategy:
    - Override the `get_repository` FastAPI dependency
    - Patch `app.api.v1.performance.session_scope` to yield a mock
      that returns our mocked repositories
    - Assert on response shape, filters, and computed fields

Test organization:
    - TestPerformanceEndpointHappyPath: successful responses
    - TestPerformanceEndpointFilters: query parameter handling
    - TestPerformanceEndpointEdgeCases: empty data, missing prices
    - TestPerformanceEndpointValidation: invalid query params
    - TestPerformanceEndpointHelpers: _as_float, _get_mean_actual_price
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ============================================================
# HELPERS
# ============================================================
def _make_metrics_row(
    model_name: str = "prophet_fresh",
    horizon: str = "24h",
    mae: float = 100.0,
    rmse: float = 120.0,
    mape: float = 1.5,
    samples: int = 480,
) -> Dict[str, Any]:
    """Build a row matching what fetch_latest_metrics_batch returns."""
    return {
        "model_name": model_name,
        "horizon": horizon,
        "model_version": "1.0.0",
        "forecast_date": datetime.now(timezone.utc),
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "samples": samples,
    }


def _make_breakdown_rows() -> List[Dict[str, Any]]:
    """Build a market breakdown result."""
    return [
        {
            "market_condition": "bull",
            "mae": 90.0,
            "rmse": 110.0,
            "mape": 1.3,
            "samples": 300,
        },
        {
            "market_condition": "bear",
            "mae": 120.0,
            "rmse": 140.0,
            "mape": 1.8,
            "samples": 180,
        },
    ]


def _mock_perf_repo(
    metrics_rows: Optional[List[Dict[str, Any]]] = None,
    breakdown_rows: Optional[List[Dict[str, Any]]] = None,
    mean_price: Optional[float] = 50_000.0,
) -> MagicMock:
    """Build a mocked PerformanceRepository."""
    repo = MagicMock()
    repo.fetch_latest_metrics_batch = AsyncMock(
        return_value=metrics_rows or []
    )
    repo.fetch_market_breakdown = AsyncMock(
        return_value=breakdown_rows if breakdown_rows is not None else _make_breakdown_rows()
    )

    # The endpoint uses perf_repo.session.execute(...).scalar_one_or_none()
    # for mean_actual_price
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mean_price
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    repo.session = mock_session

    return repo


def _mock_threshold_repo(breach_count: int = 0) -> MagicMock:
    """Build a mocked ThresholdRepository."""
    repo = MagicMock()
    repo.count_breaches = AsyncMock(return_value=breach_count)
    return repo


def _session_scope_with(perf_repo, threshold_repo) -> MagicMock:
    """Build a session_scope mock returning the given repos."""
    cm = MagicMock()

    async def _enter():
        # We return a mock session; the endpoint constructs a
        # PerformanceRepository(session) and a ThresholdRepository(session)
        # itself. To inject our mocks, we patch the repository classes.
        return MagicMock()

    cm.__aenter__ = AsyncMock(return_value=MagicMock())
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient."""
    return TestClient(app)


# ============================================================
# HAPPY PATH
# ============================================================
class TestPerformanceEndpointHappyPath:
    """Successful responses from the endpoint."""

    def test_returns_200(self, client: TestClient) -> None:
        """Test that a request returns HTTP 200."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        assert response.status_code == 200

    def test_response_has_expected_keys(self, client: TestClient) -> None:
        """Test the response envelope has the expected top-level keys."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        data = response.json()
        assert set(data.keys()) == {
            "time_period_days",
            "generated_at",
            "entries",
        }

    def test_entry_has_expected_keys(self, client: TestClient) -> None:
        """Test that each entry has the expected keys."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        entry = response.json()["entries"][0]
        expected = {
            "model_name",
            "model_version",
            "horizon",
            "samples",
            "metrics",
            "market_breakdown",
            "thresholds",
            "recent_breach_count",
            "last_updated",
        }
        assert set(entry.keys()) == expected

    def test_metrics_are_populated(self, client: TestClient) -> None:
        """Test that the metrics block contains the actual values."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row(mae=100.0, rmse=120.0, mape=1.5)],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        metrics = response.json()["entries"][0]["metrics"]
        assert metrics["mae"] == 100.0
        assert metrics["rmse"] == 120.0
        assert metrics["mape"] == 1.5
        assert metrics["directional_accuracy"] is None

    def test_market_breakdown_included(self, client: TestClient) -> None:
        """Test that the market breakdown is populated."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        breakdown = response.json()["entries"][0]["market_breakdown"]
        assert "bull" in breakdown
        assert "bear" in breakdown
        assert breakdown["bull"]["samples"] == 300

    def test_thresholds_included(self, client: TestClient) -> None:
        """Test that the thresholds block is populated."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row(mae=100.0, rmse=120.0, mape=1.5)],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        thresholds = response.json()["entries"][0]["thresholds"]
        # maep, rmse_pct, mape — directional is None so skipped
        metrics = {t["metric"] for t in thresholds}
        assert "mae_pct" in metrics
        assert "rmse_pct" in metrics
        assert "mape" in metrics

    def test_recent_breach_count_included(self, client: TestClient) -> None:
        """Test that the recent breach count is populated."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo(breach_count=3)

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        assert response.json()["entries"][0]["recent_breach_count"] == 3

    def test_multiple_entries(self, client: TestClient) -> None:
        """Test that multiple (model, horizon) pairs are returned."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[
                _make_metrics_row(model_name="prophet_fresh", horizon="24h"),
                _make_metrics_row(model_name="prophet_fresh", horizon="7d"),
                _make_metrics_row(model_name="xgboost_fresh", horizon="24h"),
            ],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        entries = response.json()["entries"]
        assert len(entries) == 3

    def test_time_period_echoed(self, client: TestClient) -> None:
        """Test that the time_period_days reflects the query param."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc?days=90")

        assert response.json()["time_period_days"] == 90


# ============================================================
# FILTERS
# ============================================================
class TestPerformanceEndpointFilters:
    """Query parameter handling."""

    def test_horizon_filter_forwarded(self, client: TestClient) -> None:
        """Test that horizon filter is passed to the repository."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row(horizon="24h")],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            client.get("/api/v1/performance/btc?horizon=24h")

        call_kwargs = perf_repo.fetch_latest_metrics_batch.call_args.kwargs
        assert call_kwargs["horizon"] == "24h"

    def test_model_name_filter_forwarded(self, client: TestClient) -> None:
        """Test that model_name filter is passed to the repository."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row(model_name="prophet_fresh")],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            client.get("/api/v1/performance/btc?model_name=prophet_fresh")

        call_kwargs = perf_repo.fetch_latest_metrics_batch.call_args.kwargs
        assert call_kwargs["model_name"] == "prophet_fresh"

    def test_days_filter_forwarded(self, client: TestClient) -> None:
        """Test that days filter is passed to the repository."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            client.get("/api/v1/performance/btc?days=90")

        call_kwargs = perf_repo.fetch_latest_metrics_batch.call_args.kwargs
        assert call_kwargs["days"] == 90


# ============================================================
# EDGE CASES
# ============================================================
class TestPerformanceEndpointEdgeCases:
    """Edge-case behavior."""

    def test_empty_metrics_returns_empty_entries(self, client: TestClient) -> None:
        """Test that no metrics returns an empty entries list."""
        perf_repo = _mock_perf_repo(metrics_rows=[])
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        assert response.status_code == 200
        assert response.json()["entries"] == []

    def test_null_mean_price_skips_mae_rmse_thresholds(
        self, client: TestClient
    ) -> None:
        """Test that when mean_actual_price is None, MAE/RMSE are not checked."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
            mean_price=None,
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        thresholds = response.json()["entries"][0]["thresholds"]
        metric_names = {t["metric"] for t in thresholds}
        # Only mape (doesn't need mean price) is checked
        assert "mae_pct" not in metric_names
        assert "rmse_pct" not in metric_names
        assert "mape" in metric_names

    def test_empty_market_breakdown(self, client: TestClient) -> None:
        """Test that an empty breakdown produces an empty dict."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
            breakdown_rows=[],
        )
        threshold_repo = _mock_threshold_repo()

        with patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ), patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ), patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ):
            response = client.get("/api/v1/performance/btc")

        assert response.json()["entries"][0]["market_breakdown"] == {}


# ============================================================
# VALIDATION
# ============================================================
class TestPerformanceEndpointValidation:
    """Invalid query parameters."""

    def test_days_zero_returns_422(self, client: TestClient) -> None:
        """Test that days=0 is rejected."""
        response = client.get("/api/v1/performance/btc?days=0")
        assert response.status_code == 422

    def test_days_over_max_returns_422(self, client: TestClient) -> None:
        """Test that days > 365 is rejected."""
        response = client.get("/api/v1/performance/btc?days=1000")
        assert response.status_code == 422

    def test_invalid_horizon_returns_422(self, client: TestClient) -> None:
        """Test that an invalid horizon is rejected."""
        response = client.get("/api/v1/performance/btc?horizon=1h")
        assert response.status_code == 422