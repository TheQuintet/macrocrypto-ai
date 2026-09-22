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
    - TestPerformanceEndpointStreakWarnings: T5.6 streak warnings
    - TestPerformanceEndpointM8BestModel: best_model on the envelope (M8)
    - TestPerformanceEndpointM8ModelsFilter: ?models= filtering (M8)
    - TestPerformanceEndpointM8History: ?include_history= behavior (M8)
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


def _make_streak_row(
    model_name: str = "prophet_fresh",
    horizon: str = "24h",
    metric: str = "mae_pct",
    consecutive_days: int = 3,
    detected_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build a row matching what fetch_latest_breaches_batch returns."""
    return {
        "model_name": model_name,
        "horizon": horizon,
        "metric": metric,
        "consecutive_days": consecutive_days,
        "detected_at": detected_at or datetime.now(timezone.utc),
    }


def _make_history_row(
    model_name: str = "prophet_fresh",
    horizon: str = "24h",
    mae: float = 100.0,
    rmse: float = 120.0,
    mape: float = 1.5,
    directional_accuracy: Optional[float] = 62.0,
    sample_size: int = 1,
    calculated_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build a row matching what ModelPerformanceRepository.fetch_history returns."""
    return {
        "model_name": model_name,
        "horizon": horizon,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "directional_accuracy": directional_accuracy,
        "sample_size": sample_size,
        "calculated_at": calculated_at or datetime.now(timezone.utc),
    }


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


def _mock_threshold_repo(
    breach_count: int = 0,
    streak_rows: Optional[List[Dict[str, Any]]] = None,
) -> MagicMock:
    """Build a mocked ThresholdRepository.

    Args:
        breach_count: Return value of count_breaches().
        streak_rows: Return value of fetch_latest_breaches_batch().
            Defaults to an empty list, meaning no warnings.
    """
    repo = MagicMock()
    repo.count_breaches = AsyncMock(return_value=breach_count)
    repo.fetch_latest_breaches_batch = AsyncMock(
        return_value=streak_rows if streak_rows is not None else []
    )
    return repo


def _mock_model_perf_repo(
    history_rows: Optional[List[Dict[str, Any]]] = None,
    best_model: Optional[str] = None,
    history_raises: Optional[Exception] = None,
) -> MagicMock:
    """Build a mocked ModelPerformanceRepository for M8 tests.

    Args:
        history_rows: Return value of fetch_history(). Defaults to [].
        best_model: Return value of fetch_best_model_by_mae().
            Defaults to None.
        history_raises: When set, fetch_history() raises this instead
            of returning a value.
    """
    repo = MagicMock()
    if history_raises is not None:
        repo.fetch_history = AsyncMock(side_effect=history_raises)
    else:
        repo.fetch_history = AsyncMock(return_value=history_rows or [])
    repo.fetch_best_model_by_mae = AsyncMock(return_value=best_model)
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


def _patch_stack(
    perf_repo: MagicMock,
    threshold_repo: MagicMock,
    model_perf_repo: Optional[MagicMock] = None,
):
    """Return a tuple of patch context managers for the three repos.

    When `model_perf_repo` is None, a default empty one is created.

    Usage:
        with _patch_stack(perf, threshold) as (p1, p2, p3, p4):
            ...

    The order is: PerformanceRepository, ThresholdRepository,
    ModelPerformanceRepository, session_scope. These must be entered
    together because the endpoint uses all four.
    """
    if model_perf_repo is None:
        model_perf_repo = _mock_model_perf_repo()

    return (
        patch(
            "app.api.v1.performance.PerformanceRepository",
            return_value=perf_repo,
        ),
        patch(
            "app.api.v1.performance.ThresholdRepository",
            return_value=threshold_repo,
        ),
        patch(
            "app.api.v1.performance.ModelPerformanceRepository",
            return_value=model_perf_repo,
        ),
        patch(
            "app.api.v1.performance.session_scope",
            return_value=_session_scope_with(perf_repo, threshold_repo),
        ),
    )


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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        assert response.status_code == 200

    def test_response_has_expected_keys(self, client: TestClient) -> None:
        """Test the response envelope has the expected top-level keys."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        data = response.json()
        assert set(data.keys()) == {
            "time_period_days",
            "generated_at",
            "entries",
            "warnings_count",
            "best_model",
        }

    def test_entry_has_expected_keys(self, client: TestClient) -> None:
        """Test that each entry has the expected keys."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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
            "warning",
            "warning_count",
            "warning_threshold_days",
            "history",
        }
        assert set(entry.keys()) == expected

    def test_metrics_are_populated(self, client: TestClient) -> None:
        """Test that the metrics block contains the actual values."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row(mae=100.0, rmse=120.0, mape=1.5)],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        entries = response.json()["entries"]
        assert len(entries) == 3

    def test_time_period_echoed(self, client: TestClient) -> None:
        """Test that the time_period_days reflects the query param."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            client.get("/api/v1/performance/btc?horizon=24h")

        call_kwargs = perf_repo.fetch_latest_metrics_batch.call_args.kwargs
        assert call_kwargs["horizon"] == "24h"

    def test_model_name_filter_restricts_entries(
        self, client: TestClient
    ) -> None:
        """Test that ?model_name= restricts the returned entries.

        M8 changed the filtering strategy: the endpoint fetches all
        rows from the repository and filters Python-side, because
        `fetch_latest_metrics_batch` only accepts a single-model
        filter and adding an IN-style parameter would be out of
        scope. We therefore assert on the effect (only the
        requested model appears), not on a repository kwarg.
        """
        perf_repo = _mock_perf_repo(
            metrics_rows=[
                _make_metrics_row(model_name="prophet_fresh"),
                _make_metrics_row(model_name="xgboost_fresh"),
            ],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get(
                "/api/v1/performance/btc?model_name=prophet_fresh"
            )

        entries = response.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["model_name"] == "prophet_fresh"

    def test_days_filter_forwarded(self, client: TestClient) -> None:
        """Test that days filter is passed to the repository."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
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


# ============================================================
# STREAK WARNINGS (T5.6)
# ============================================================
class TestPerformanceEndpointStreakWarnings:
    """Tests for T5.6 streak-warning surfacing in the response."""

    def test_no_warning_when_no_streaks(self, client: TestClient) -> None:
        """Test that an empty streak list yields warning=False."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo(streak_rows=[])

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        body = response.json()
        entry = body["entries"][0]
        assert entry["warning"] is False
        assert entry["warning_count"] == 0
        assert entry["warning_threshold_days"] == 3
        assert body["warnings_count"] == 0

    def test_warning_surfaced_when_streak_met(
        self, client: TestClient
    ) -> None:
        """Test that a 3-day streak produces warning=True on the entry."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo(
            streak_rows=[
                _make_streak_row(
                    metric="mae_pct", consecutive_days=3
                )
            ],
        )

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        body = response.json()
        entry = body["entries"][0]
        assert entry["warning"] is True
        assert entry["warning_count"] == 1
        assert entry["warning_threshold_days"] == 3
        assert body["warnings_count"] == 1

    def test_warning_not_surfaced_below_streak(
        self, client: TestClient
    ) -> None:
        """Test that a 2-day streak does NOT produce a warning."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo(
            streak_rows=[
                _make_streak_row(
                    metric="mae_pct", consecutive_days=2
                )
            ],
        )

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        entry = response.json()["entries"][0]
        assert entry["warning"] is False
        assert entry["warning_count"] == 0

    def test_per_metric_consecutive_days_surfaced(
        self, client: TestClient
    ) -> None:
        """Test that streak days are surfaced on the matching metric."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo(
            streak_rows=[
                _make_streak_row(
                    metric="mae_pct", consecutive_days=3
                )
            ],
        )

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        entry = response.json()["entries"][0]
        mae_status = next(
            t for t in entry["thresholds"] if t["metric"] == "mae_pct"
        )
        assert mae_status["consecutive_days"] == 3
        assert mae_status["warning"] is True

    def test_warnings_count_sums_metrics_not_entries(
        self, client: TestClient
    ) -> None:
        """Test that warnings_count is the total warned metrics, not entries.

        One entry with two warned metrics must contribute 2 to the
        envelope's `warnings_count`.
        """
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo(
            streak_rows=[
                _make_streak_row(
                    metric="mae_pct", consecutive_days=3
                ),
                _make_streak_row(
                    metric="rmse_pct", consecutive_days=4
                ),
            ],
        )

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        body = response.json()
        assert body["entries"][0]["warning_count"] == 2
        assert body["warnings_count"] == 2

    def test_breach_today_no_recorded_streak_no_warning(
        self, client: TestClient
    ) -> None:
        """Test that a metric breaching today with no recorded streak
        does not warn.

        Design intent: the warning requires 3 *recorded* consecutive
        days in `threshold_breaches`. On day 1 of a fresh breach there
        is no history yet, so `consecutive_days` is 0 and no warning
        fires — even though `breached` is True.

        Here we set MAE way above 10% of mean price → breached=True,
        but seed no streak rows → no warning.
        """
        perf_repo = _mock_perf_repo(
            # 500 USD on 50000 mean = 1% — to make MAE actually breach
            # we need to bump it above 10% (5000 USD).
            metrics_rows=[
                _make_metrics_row(mae=6_000.0, rmse=120.0, mape=1.5)
            ],
            mean_price=50_000.0,
        )
        threshold_repo = _mock_threshold_repo(streak_rows=[])

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        entry = response.json()["entries"][0]
        mae_status = next(
            t for t in entry["thresholds"] if t["metric"] == "mae_pct"
        )
        assert mae_status["breached"] is True
        assert mae_status["consecutive_days"] == 0
        assert mae_status["warning"] is False
        assert entry["warning"] is False
        assert entry["warning_count"] == 0

    def test_streak_grouped_by_model_and_horizon(
        self, client: TestClient
    ) -> None:
        """Test that a streak for model A/horizon X does not warn model B/horizon Y."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[
                _make_metrics_row(
                    model_name="prophet_fresh", horizon="24h"
                ),
                _make_metrics_row(
                    model_name="xgboost_fresh", horizon="7d"
                ),
            ],
        )
        # Only prophet_fresh/24h has a streak.
        threshold_repo = _mock_threshold_repo(
            streak_rows=[
                _make_streak_row(
                    model_name="prophet_fresh",
                    horizon="24h",
                    metric="mae_pct",
                    consecutive_days=3,
                )
            ],
        )

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        entries = {
            (e["model_name"], e["horizon"]): e
            for e in response.json()["entries"]
        }
        assert entries[("prophet_fresh", "24h")]["warning"] is True
        assert entries[("xgboost_fresh", "7d")]["warning"] is False

    def test_multiple_entries_warnings_count_is_total(
        self, client: TestClient
    ) -> None:
        """Test that envelope warnings_count sums across entries."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[
                _make_metrics_row(
                    model_name="prophet_fresh", horizon="24h"
                ),
                _make_metrics_row(
                    model_name="xgboost_fresh", horizon="24h"
                ),
            ],
        )
        threshold_repo = _mock_threshold_repo(
            streak_rows=[
                _make_streak_row(
                    model_name="prophet_fresh",
                    horizon="24h",
                    metric="mae_pct",
                    consecutive_days=3,
                ),
                _make_streak_row(
                    model_name="xgboost_fresh",
                    horizon="24h",
                    metric="mae_pct",
                    consecutive_days=3,
                ),
                _make_streak_row(
                    model_name="xgboost_fresh",
                    horizon="24h",
                    metric="mape",
                    consecutive_days=4,
                ),
            ],
        )

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get("/api/v1/performance/btc")

        body = response.json()
        # 1 warning for prophet, 2 for xgboost → 3 total
        assert body["warnings_count"] == 3


# ============================================================
# M8 — BEST MODEL ON THE ENVELOPE
# ============================================================
class TestPerformanceEndpointM8BestModel:
    """Tests for the additive best_model field (M8)."""

    def test_best_model_populated_when_entries_exist(
        self, client: TestClient
    ) -> None:
        """Test that best_model is populated when entries exist."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()
        model_perf_repo = _mock_model_perf_repo(best_model="prophet_fresh")

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get("/api/v1/performance/btc")

        assert response.status_code == 200
        assert response.json()["best_model"] == "prophet_fresh"

    def test_best_model_none_when_no_entries(
        self, client: TestClient
    ) -> None:
        """Test that best_model is None when there are no entries.

        The endpoint skips the best-model query when entries is
        empty, so the field is None even if the repository would
        return a value.
        """
        perf_repo = _mock_perf_repo(metrics_rows=[])
        threshold_repo = _mock_threshold_repo()
        model_perf_repo = _mock_model_perf_repo(best_model="prophet_fresh")

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get("/api/v1/performance/btc")

        body = response.json()
        assert body["entries"] == []
        assert body["best_model"] is None
        # Repository was never consulted
        assert model_perf_repo.fetch_best_model_by_mae.call_count == 0

    def test_best_model_none_when_repo_returns_none(
        self, client: TestClient
    ) -> None:
        """Test that best_model is None when the repo has no MAE data."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()
        model_perf_repo = _mock_model_perf_repo(best_model=None)

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get("/api/v1/performance/btc")

        assert response.json()["best_model"] is None

    def test_best_model_lookup_error_is_swallowed(
        self, client: TestClient
    ) -> None:
        """Test that a repo error during best-model lookup does not 500.

        Best model is a convenience field — losing it must not break
        the response. The endpoint catches the exception, logs a
        warning, and returns best_model=None.
        """
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()

        model_perf_repo = MagicMock()
        model_perf_repo.fetch_best_model_by_mae = AsyncMock(
            side_effect=RuntimeError("DB down")
        )

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get("/api/v1/performance/btc")

        assert response.status_code == 200
        assert response.json()["best_model"] is None


# ============================================================
# M8 — ?models= FILTER
# ============================================================
class TestPerformanceEndpointM8ModelsFilter:
    """Tests for the ?models= comma-separated filter (M8)."""

    def test_models_filters_to_single_model(
        self, client: TestClient
    ) -> None:
        """Test that ?models=a returns only model a."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[
                _make_metrics_row(model_name="prophet_fresh"),
                _make_metrics_row(model_name="xgboost_fresh"),
            ],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get(
                "/api/v1/performance/btc?models=prophet_fresh"
            )

        entries = response.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["model_name"] == "prophet_fresh"

    def test_models_filters_to_multiple_models(
        self, client: TestClient
    ) -> None:
        """Test that ?models=a,b returns only a and b."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[
                _make_metrics_row(model_name="prophet_fresh"),
                _make_metrics_row(model_name="xgboost_fresh"),
                _make_metrics_row(model_name="lightgbm_fresh"),
            ],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get(
                "/api/v1/performance/btc"
                "?models=prophet_fresh,xgboost_fresh"
            )

        entries = response.json()["entries"]
        names = {e["model_name"] for e in entries}
        assert names == {"prophet_fresh", "xgboost_fresh"}

    def test_models_unknown_names_silently_ignored(
        self, client: TestClient
    ) -> None:
        """Test that unknown model names in ?models= are silently dropped.

        Matches the M6a convention: well-formed unknown names are not
        errors. The response simply has no entry for them.
        """
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row(model_name="prophet_fresh")],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get(
                "/api/v1/performance/btc?models=prophet_fresh,ghost"
            )

        assert response.status_code == 200
        entries = response.json()["entries"]
        assert len(entries) == 1
        assert entries[0]["model_name"] == "prophet_fresh"

    def test_models_duplicates_deduplicated(
        self, client: TestClient
    ) -> None:
        """Test that ?models=a,a is treated as ?models=a (no 422)."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row(model_name="prophet_fresh")],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get(
                "/api/v1/performance/btc"
                "?models=prophet_fresh,prophet_fresh"
            )

        assert response.status_code == 200
        assert len(response.json()["entries"]) == 1

    def test_models_empty_segment_returns_422(
        self, client: TestClient
    ) -> None:
        """Test that a doubled comma in ?models= returns 422."""
        response = client.get(
            "/api/v1/performance/btc?models=a,,b"
        )
        assert response.status_code == 422

    def test_models_and_model_name_both_given_models_wins(
        self, client: TestClient
    ) -> None:
        """Test that ?models= wins over ?model_name= when both are given.

        This is a deliberate ergonomic choice: clients shouldn't have
        to know which parameter to send. The endpoint logs a warning
        so operators can spot the confusion.
        """
        perf_repo = _mock_perf_repo(
            metrics_rows=[
                _make_metrics_row(model_name="prophet_fresh"),
                _make_metrics_row(model_name="xgboost_fresh"),
            ],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get(
                "/api/v1/performance/btc"
                "?models=prophet_fresh"
                "&model_name=xgboost_fresh"
            )

        assert response.status_code == 200
        entries = response.json()["entries"]
        # models= wins, so only prophet_fresh appears
        assert len(entries) == 1
        assert entries[0]["model_name"] == "prophet_fresh"

    def test_models_whitespace_only_treated_as_unset(
        self, client: TestClient
    ) -> None:
        """Test that ?models=%20 returns every entry (no filter)."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[
                _make_metrics_row(model_name="prophet_fresh"),
                _make_metrics_row(model_name="xgboost_fresh"),
            ],
        )
        threshold_repo = _mock_threshold_repo()

        with _patch_stack(perf_repo, threshold_repo)[0], \
             _patch_stack(perf_repo, threshold_repo)[1], \
             _patch_stack(perf_repo, threshold_repo)[2], \
             _patch_stack(perf_repo, threshold_repo)[3]:
            response = client.get(
                "/api/v1/performance/btc?models=%20"
            )

        assert response.status_code == 200
        assert len(response.json()["entries"]) == 2


# ============================================================
# M8 — ?include_history= BEHAVIOR
# ============================================================
class TestPerformanceEndpointM8History:
    """Tests for the ?include_history= opt-in flag (M8)."""

    def test_history_empty_by_default(self, client: TestClient) -> None:
        """Test that entries have history=[] when the flag is off."""
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()
        model_perf_repo = _mock_model_perf_repo(
            history_rows=[_make_history_row()]
        )

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get("/api/v1/performance/btc")

        entry = response.json()["entries"][0]
        assert entry["history"] == []
        # History repository was never consulted
        assert model_perf_repo.fetch_history.call_count == 0

    def test_history_included_when_flag_on(
        self, client: TestClient
    ) -> None:
        """Test that ?include_history=true attaches history to each entry."""
        now = datetime.now(timezone.utc)
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()
        model_perf_repo = _mock_model_perf_repo(
            history_rows=[
                _make_history_row(
                    mae=100.0,
                    calculated_at=now - timedelta(days=1),
                ),
                _make_history_row(
                    mae=110.0,
                    calculated_at=now,
                ),
            ]
        )

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get(
                "/api/v1/performance/btc?include_history=true"
            )

        entry = response.json()["entries"][0]
        assert len(entry["history"]) == 2
        assert entry["history"][0]["mae"] == 100.0
        assert entry["history"][1]["mae"] == 110.0

    def test_history_limit_truncates_to_most_recent(
        self, client: TestClient
    ) -> None:
        """Test that ?history_limit=N keeps the most recent N points."""
        now = datetime.now(timezone.utc)
        rows = [
            _make_history_row(
                mae=float(i),
                calculated_at=now - timedelta(days=10 - i),
            )
            for i in range(10)
        ]
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()
        model_perf_repo = _mock_model_perf_repo(history_rows=rows)

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get(
                "/api/v1/performance/btc"
                "?include_history=true&history_limit=3"
            )

        entry = response.json()["entries"][0]
        assert len(entry["history"]) == 3
        # Most recent three: mae = 7.0, 8.0, 9.0 (ascending order preserved)
        assert [p["mae"] for p in entry["history"]] == [7.0, 8.0, 9.0]

    def test_history_ordered_ascending_by_calculated_at(
        self, client: TestClient
    ) -> None:
        """Test that history points are returned oldest-first."""
        now = datetime.now(timezone.utc)
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()
        model_perf_repo = _mock_model_perf_repo(
            history_rows=[
                _make_history_row(
                    mae=100.0,
                    calculated_at=now - timedelta(days=2),
                ),
                _make_history_row(
                    mae=110.0,
                    calculated_at=now - timedelta(days=1),
                ),
                _make_history_row(
                    mae=120.0,
                    calculated_at=now,
                ),
            ]
        )

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get(
                "/api/v1/performance/btc?include_history=true"
            )

        entry = response.json()["entries"][0]
        times = [p["calculated_at"] for p in entry["history"]]
        assert times == sorted(times)
        assert [p["mae"] for p in entry["history"]] == [100.0, 110.0, 120.0]

    def test_history_repo_error_is_swallowed(
        self, client: TestClient
    ) -> None:
        """Test that a history fetch error yields history=[] but 200 OK.

        History is opt-in and best-effort. If the underlying query
        fails, the entry still appears with an empty history and the
        rest of the response is unaffected.
        """
        perf_repo = _mock_perf_repo(
            metrics_rows=[_make_metrics_row()],
        )
        threshold_repo = _mock_threshold_repo()
        model_perf_repo = _mock_model_perf_repo(
            history_raises=RuntimeError("history query failed")
        )

        patches = _patch_stack(perf_repo, threshold_repo, model_perf_repo)
        with patches[0], patches[1], patches[2], patches[3]:
            response = client.get(
                "/api/v1/performance/btc?include_history=true"
            )

        assert response.status_code == 200
        entry = response.json()["entries"][0]
        assert entry["history"] == []
        # Other fields still populated
        assert entry["model_name"] == "prophet_fresh"