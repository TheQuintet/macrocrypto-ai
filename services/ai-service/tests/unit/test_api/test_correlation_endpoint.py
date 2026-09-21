"""Unit tests for the GET /api/v1/correlation/btc endpoint.

These tests use FastAPI's TestClient with a mocked
CorrelationRepository so no live database is required.

Strategy:
    - Patch `app.api.v1.correlation.session_scope` to yield a mock
      session
    - Patch `app.api.v1.correlation.CorrelationRepository` to
      return our mocked repository
    - Assert on response shape, filters, derived fields, and
      history behavior

Test organization:
    - TestCorrelationEndpointHappyPath: successful responses
    - TestCorrelationEndpointDerivedFields: color, arrow,
      significance, confidence, insight populated correctly
    - TestCorrelationEndpointWindowFilter: ?window_days=
    - TestCorrelationEndpointHistory: ?include_history=,
      ?history_limit=, ?history_days=
    - TestCorrelationEndpointEdgeCases: empty results, error
      isolation
    - TestCorrelationEndpointValidation: invalid query params
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
def _make_latest_row(
    indicator_name: str = "inflation",
    window_days: int = 90,
    coefficient: float = -0.42,
    strength: str = "medium",
    direction: str = "negative",
    p_value: Optional[float] = 0.03,
) -> Dict[str, Any]:
    """Build a row matching what fetch_latest_per_indicator returns."""
    return {
        "indicator_name": indicator_name,
        "window_days": window_days,
        "calculated_at": datetime.now(timezone.utc),
        "correlation_coefficient": coefficient,
        "strength": strength,
        "direction": direction,
        "p_value": p_value,
        "created_at": datetime.now(timezone.utc),
    }


def _make_history_row(
    indicator_name: str = "inflation",
    window_days: int = 90,
    coefficient: float = -0.40,
    strength: str = "medium",
    direction: str = "negative",
    p_value: Optional[float] = 0.04,
    calculated_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build a row matching what fetch_history returns."""
    return {
        "indicator_name": indicator_name,
        "window_days": window_days,
        "calculated_at": calculated_at or datetime.now(timezone.utc),
        "correlation_coefficient": coefficient,
        "strength": strength,
        "direction": direction,
        "p_value": p_value,
    }


def _mock_correlation_repo(
    latest_rows: Optional[List[Dict[str, Any]]] = None,
    history_rows: Optional[List[Dict[str, Any]]] = None,
    latest_raises: Optional[Exception] = None,
    history_raises: Optional[Exception] = None,
) -> MagicMock:
    """Build a mocked CorrelationRepository."""
    repo = MagicMock()

    if latest_raises is not None:
        repo.fetch_latest_per_indicator = AsyncMock(
            side_effect=latest_raises
        )
    else:
        repo.fetch_latest_per_indicator = AsyncMock(
            return_value=latest_rows if latest_rows is not None else []
        )

    if history_raises is not None:
        repo.fetch_history = AsyncMock(side_effect=history_raises)
    else:
        repo.fetch_history = AsyncMock(
            return_value=history_rows if history_rows is not None else []
        )

    return repo


def _session_scope_mock() -> MagicMock:
    """Build a session_scope mock."""
    cm = MagicMock()
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
class TestCorrelationEndpointHappyPath:
    """Successful responses from the endpoint."""

    def test_returns_200(self, client: TestClient) -> None:
        """Test that a valid request returns HTTP 200."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        assert response.status_code == 200

    def test_response_has_expected_keys(
        self, client: TestClient
    ) -> None:
        """Test the envelope has the expected top-level keys."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        data = response.json()
        assert set(data.keys()) == {
            "window_days",
            "generated_at",
            "entries",
        }

    def test_entry_has_expected_keys(self, client: TestClient) -> None:
        """Test that each entry has the expected keys."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        entry = response.json()["entries"][0]
        expected = {
            "indicator_name",
            "window_days",
            "correlation_coefficient",
            "strength",
            "strength_color",
            "direction",
            "direction_arrow",
            "p_value",
            "is_significant",
            "confidence_level",
            "calculated_at",
            "insight",
            "history",
        }
        assert set(entry.keys()) == expected

    def test_multiple_indicators_returned(
        self, client: TestClient
    ) -> None:
        """Test that each indicator gets its own entry."""
        repo = _mock_correlation_repo(
            latest_rows=[
                _make_latest_row(indicator_name="inflation"),
                _make_latest_row(indicator_name="rates"),
            ],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        entries = response.json()["entries"]
        assert len(entries) == 2
        names = {e["indicator_name"] for e in entries}
        assert names == {"inflation", "rates"}

    def test_window_days_echoed(self, client: TestClient) -> None:
        """Test that the requested window_days is echoed in the response."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row(window_days=30)],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get(
                "/api/v1/correlation/btc?window_days=30"
            )

        assert response.json()["window_days"] == 30


# ============================================================
# DERIVED FIELDS
# ============================================================
class TestCorrelationEndpointDerivedFields:
    """Tests for the derived presentation fields."""

    def test_strong_negative_populates_green_and_down_arrow(
        self, client: TestClient
    ) -> None:
        """A strong negative correlation maps to green + ↓."""
        repo = _mock_correlation_repo(
            latest_rows=[
                _make_latest_row(
                    coefficient=-0.85,
                    strength="strong",
                    direction="negative",
                    p_value=0.001,
                )
            ],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        entry = response.json()["entries"][0]
        assert entry["strength"] == "strong"
        assert entry["strength_color"] == "green"
        assert entry["direction"] == "negative"
        assert entry["direction_arrow"] == "↓"
        assert entry["is_significant"] is True
        assert entry["confidence_level"] == pytest.approx(99.9)

    def test_weak_positive_populates_red_and_up_arrow(
        self, client: TestClient
    ) -> None:
        """A weak positive correlation maps to red + ↑."""
        repo = _mock_correlation_repo(
            latest_rows=[
                _make_latest_row(
                    coefficient=0.1,
                    strength="weak",
                    direction="positive",
                    p_value=0.5,
                )
            ],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        entry = response.json()["entries"][0]
        assert entry["strength"] == "weak"
        assert entry["strength_color"] == "red"
        assert entry["direction"] == "positive"
        assert entry["direction_arrow"] == "↑"
        assert entry["is_significant"] is False
        assert entry["confidence_level"] == pytest.approx(50.0)

    def test_none_p_value_yields_false_and_none(
        self, client: TestClient
    ) -> None:
        """A None p_value yields is_significant=False and confidence=None."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row(p_value=None)],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        entry = response.json()["entries"][0]
        assert entry["p_value"] is None
        assert entry["is_significant"] is False
        assert entry["confidence_level"] is None

    def test_insight_populated(self, client: TestClient) -> None:
        """Test that each entry carries a non-empty insight sentence."""
        repo = _mock_correlation_repo(
            latest_rows=[
                _make_latest_row(
                    indicator_name="inflation",
                    coefficient=-0.42,
                    strength="medium",
                    direction="negative",
                    p_value=0.03,
                )
            ],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        entry = response.json()["entries"][0]
        assert "inflation" in entry["insight"]
        assert "falls" in entry["insight"]
        assert "medium" in entry["insight"]
        assert "confidence" in entry["insight"]

    def test_insight_drops_confidence_when_p_value_none(
        self, client: TestClient
    ) -> None:
        """Test that a None p-value drops the confidence clause."""
        repo = _mock_correlation_repo(
            latest_rows=[
                _make_latest_row(
                    indicator_name="rates",
                    coefficient=0.5,
                    strength="medium",
                    direction="positive",
                    p_value=None,
                )
            ],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        entry = response.json()["entries"][0]
        assert "rates" in entry["insight"]
        assert "rises" in entry["insight"]
        assert "confidence" not in entry["insight"]


# ============================================================
# WINDOW FILTER
# ============================================================
class TestCorrelationEndpointWindowFilter:
    """Tests for the ?window_days= parameter."""

    def test_default_window_is_90(self, client: TestClient) -> None:
        """Test that the default window_days is 90."""
        repo = _mock_correlation_repo(latest_rows=[])

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            client.get("/api/v1/correlation/btc")

        kwargs = repo.fetch_latest_per_indicator.call_args.kwargs
        assert kwargs["window_days"] == 90

    def test_window_30_forwarded(self, client: TestClient) -> None:
        """Test that ?window_days=30 is forwarded to the repository."""
        repo = _mock_correlation_repo(latest_rows=[])

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            client.get("/api/v1/correlation/btc?window_days=30")

        kwargs = repo.fetch_latest_per_indicator.call_args.kwargs
        assert kwargs["window_days"] == 30

    def test_window_365_forwarded(self, client: TestClient) -> None:
        """Test that ?window_days=365 is forwarded to the repository."""
        repo = _mock_correlation_repo(latest_rows=[])

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            client.get("/api/v1/correlation/btc?window_days=365")

        kwargs = repo.fetch_latest_per_indicator.call_args.kwargs
        assert kwargs["window_days"] == 365


# ============================================================
# HISTORY
# ============================================================
class TestCorrelationEndpointHistory:
    """Tests for the ?include_history= behavior."""

    def test_history_empty_by_default(self, client: TestClient) -> None:
        """Test that entries have history=[] when the flag is off."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
            history_rows=[_make_history_row()],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        entry = response.json()["entries"][0]
        assert entry["history"] == []
        # Repository was never asked for history
        assert repo.fetch_history.call_count == 0

    def test_history_attached_when_flagged(
        self, client: TestClient
    ) -> None:
        """Test that ?include_history=true attaches history."""
        now = datetime.now(timezone.utc)
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
            history_rows=[
                _make_history_row(
                    coefficient=-0.40,
                    calculated_at=now - timedelta(days=1),
                ),
                _make_history_row(
                    coefficient=-0.42,
                    calculated_at=now,
                ),
            ],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get(
                "/api/v1/correlation/btc?include_history=true"
            )

        entry = response.json()["entries"][0]
        assert len(entry["history"]) == 2
        # Oldest first
        assert entry["history"][0]["correlation_coefficient"] == -0.40
        assert entry["history"][1]["correlation_coefficient"] == -0.42

    def test_history_points_have_derived_fields(
        self, client: TestClient
    ) -> None:
        """Test that history points carry the derived display fields."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
            history_rows=[
                _make_history_row(
                    coefficient=-0.85,
                    strength="strong",
                    direction="negative",
                    p_value=0.001,
                )
            ],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get(
                "/api/v1/correlation/btc?include_history=true"
            )

        point = response.json()["entries"][0]["history"][0]
        assert point["strength_color"] == "green"
        assert point["direction_arrow"] == "↓"
        assert point["is_significant"] is True
        assert point["confidence_level"] == pytest.approx(99.9)
        # The identifiers are NOT on history points
        assert "indicator_name" not in point
        assert "window_days" not in point

    def test_history_limit_truncates_to_most_recent(
        self, client: TestClient
    ) -> None:
        """Test that history_limit keeps the most recent N points."""
        now = datetime.now(timezone.utc)
        rows = [
            _make_history_row(
                coefficient=float(i),
                calculated_at=now - timedelta(days=10 - i),
            )
            for i in range(10)
        ]
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
            history_rows=rows,
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get(
                "/api/v1/correlation/btc"
                "?include_history=true&history_limit=3"
            )

        history = response.json()["entries"][0]["history"]
        assert len(history) == 3
        # Most recent three: coefficients 7.0, 8.0, 9.0
        assert [
            p["correlation_coefficient"] for p in history
        ] == [7.0, 8.0, 9.0]

    def test_history_days_forwarded(self, client: TestClient) -> None:
        """Test that history_days is forwarded to fetch_history."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
            history_rows=[],
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            client.get(
                "/api/v1/correlation/btc"
                "?include_history=true&history_days=180"
            )

        kwargs = repo.fetch_history.call_args.kwargs
        assert kwargs["days"] == 180


# ============================================================
# EDGE CASES
# ============================================================
class TestCorrelationEndpointEdgeCases:
    """Edge-case behavior."""

    def test_empty_results_returns_200_with_empty_entries(
        self, client: TestClient
    ) -> None:
        """Test that no rows returns 200 with an empty entries list."""
        repo = _mock_correlation_repo(latest_rows=[])

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get("/api/v1/correlation/btc")

        assert response.status_code == 200
        assert response.json()["entries"] == []

    def test_history_fetch_error_degrades_to_empty(
        self, client: TestClient
    ) -> None:
        """Test that a history fetch error yields history=[] but 200 OK."""
        repo = _mock_correlation_repo(
            latest_rows=[_make_latest_row()],
            history_raises=RuntimeError("history query failed"),
        )

        with patch(
            "app.api.v1.correlation.CorrelationRepository",
            return_value=repo,
        ), patch(
            "app.api.v1.correlation.session_scope",
            return_value=_session_scope_mock(),
        ):
            response = client.get(
                "/api/v1/correlation/btc?include_history=true"
            )

        assert response.status_code == 200
        entry = response.json()["entries"][0]
        assert entry["history"] == []
        assert entry["indicator_name"] == "inflation"


# ============================================================
# VALIDATION
# ============================================================
class TestCorrelationEndpointValidation:
    """Invalid query parameters."""

    def test_invalid_window_45_returns_422(
        self, client: TestClient
    ) -> None:
        """Test that window_days=45 is rejected."""
        response = client.get("/api/v1/correlation/btc?window_days=45")
        assert response.status_code == 422

    def test_invalid_window_0_returns_422(
        self, client: TestClient
    ) -> None:
        """Test that window_days=0 is rejected."""
        response = client.get("/api/v1/correlation/btc?window_days=0")
        assert response.status_code == 422

    def test_invalid_window_1000_returns_422(
        self, client: TestClient
    ) -> None:
        """Test that window_days=1000 is rejected."""
        response = client.get(
            "/api/v1/correlation/btc?window_days=1000"
        )
        assert response.status_code == 422

    def test_invalid_history_limit_returns_422(
        self, client: TestClient
    ) -> None:
        """Test that history_limit above the max is rejected."""
        response = client.get(
            "/api/v1/correlation/btc?history_limit=1000"
        )
        assert response.status_code == 422

    def test_invalid_history_days_returns_422(
        self, client: TestClient
    ) -> None:
        """Test that history_days above the max is rejected."""
        response = client.get(
            "/api/v1/correlation/btc?history_days=1000"
        )
        assert response.status_code == 422