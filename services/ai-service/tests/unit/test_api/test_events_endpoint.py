"""Unit tests for the events endpoint (A5.4).

Exercises GET /api/v1/events/historical through FastAPI's
TestClient. The service layer is mocked, so no database or Redis
is required.

Covers:
    - Happy path: unfiltered request returns events + metrics
    - event_type filter: single, multiple, invalid values
    - Date range filter: valid range, reversed range (422)
    - Combined filters
    - Empty results (200 with empty lists, not 404)
    - Response shape: events, by_type, unmapped_names,
      insufficient, count, filters, generated_at
    - Cache behavior: hit and miss (Redis mocked)
    - OpenAPI documentation
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.events.metrics import EventTypeMetrics
from app.main import app


# ============================================================
# HELPERS
# ============================================================
def _row(
    name: str,
    day: int,
    change: float,
    vol: float = 1.0,
    direction: str = "up",
) -> Dict[str, Any]:
    """Build a dict shaped like a historical_event_impacts row."""
    return {
        "event_name": name,
        "event_date": date(2024, 3, day),
        "impact_level": "high",
        "btc_price_before": 60000.0,
        "btc_price_after": 60000.0 + change * 600.0,
        "price_change_percent": change,
        "volatility": vol,
        "direction": direction,
    }


def _metrics_for(event_type: str, n: int) -> EventTypeMetrics:
    """Build a plausible EventTypeMetrics for a type."""
    return EventTypeMetrics(
        event_type=event_type,
        n_events=n,
        mean_change=1.5,
        mean_volatility=1.0,
        direction_frequencies={"up": 0.5, "down": 0.25, "neutral": 0.25},
        min_change=-1.0,
        max_change=4.0,
        mean_change_ci=(-0.5, 3.5),
        confidence_level=0.95,
    )


def _fake_service_payload(
    events: Optional[List[Dict[str, Any]]] = None,
    by_type: Optional[Dict[str, EventTypeMetrics]] = None,
    unmapped: Optional[List[str]] = None,
    insufficient: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build the dict that fetch_historical_events would return."""
    events = events or []
    return {
        "generated_at": datetime(2026, 9, 16, tzinfo=timezone.utc),
        "count": len(events),
        "events": events,
        "by_type": by_type or {},
        "unmapped_names": unmapped or [],
        "insufficient": insufficient or [],
    }


@pytest.fixture
def client() -> TestClient:
    """TestClient with the app, no lifespan (no scheduler/Redis)."""
    return TestClient(app)


# ============================================================
# HAPPY PATH
# ============================================================
class TestEventsEndpointHappyPath:
    """Unfiltered requests return the full payload."""

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_returns_200(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload(
            events=[_row("FOMC", 20, 3.0)],
            by_type={"fed": _metrics_for("fed", 1)},
        )

        resp = client.get("/api/v1/events/historical")

        assert resp.status_code == 200

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_response_shape(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload(
            events=[_row("FOMC", 20, 3.0)],
            by_type={"fed": _metrics_for("fed", 1)},
        )

        resp = client.get("/api/v1/events/historical")
        body = resp.json()

        assert set(body.keys()) == {
            "generated_at",
            "count",
            "filters",
            "events",
            "by_type",
            "unmapped_names",
            "insufficient",
        }
        assert body["count"] == 1
        assert len(body["events"]) == 1
        assert "fed" in body["by_type"]

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_event_fields(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload(
            events=[_row("FOMC", 20, 3.0)],
        )

        resp = client.get("/api/v1/events/historical")
        event = resp.json()["events"][0]

        assert event["event_name"] == "FOMC"
        assert event["event_date"] == "2024-03-20"
        assert event["impact_level"] == "high"
        assert event["direction"] == "up"

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_metrics_fields(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload(
            by_type={"fed": _metrics_for("fed", 4)},
        )

        resp = client.get("/api/v1/events/historical")
        m = resp.json()["by_type"]["fed"]

        assert m["event_type"] == "fed"
        assert m["n_events"] == 4
        assert m["direction_frequencies"] == {
            "up": 0.5, "down": 0.25, "neutral": 0.25
        }
        assert m["mean_change_ci"] == [-0.5, 3.5]
        assert m["confidence_level"] == 0.95


# ============================================================
# FILTERING
# ============================================================
class TestEventsEndpointFiltering:
    """event_type and date range filters."""

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_single_event_type_forwarded(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload()

        client.get("/api/v1/events/historical?event_type=fed")

        kwargs = mock_fetch.call_args.kwargs
        assert kwargs["event_type"] == ["fed"]

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_multiple_event_types_forwarded(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload()

        client.get("/api/v1/events/historical?event_type=fed&event_type=cpi")

        kwargs = mock_fetch.call_args.kwargs
        assert set(kwargs["event_type"]) == {"fed", "cpi"}

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    def test_invalid_event_type_returns_422(
        self, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None

        resp = client.get("/api/v1/events/historical?event_type=bogus")

        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"]["error"] == "invalid_event_type"
        assert "bogus" in body["detail"]["message"]

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_date_range_forwarded(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload()

        client.get(
            "/api/v1/events/historical"
            "?start_date=2024-01-01&end_date=2024-12-31"
        )

        kwargs = mock_fetch.call_args.kwargs
        assert kwargs["start_date"] == date(2024, 1, 1)
        assert kwargs["end_date"] == date(2024, 12, 31)

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    def test_reversed_dates_return_422(
        self, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None

        resp = client.get(
            "/api/v1/events/historical"
            "?start_date=2024-12-31&end_date=2024-01-01"
        )

        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"]["error"] == "invalid_date_range"

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_filters_echoed_in_response(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload()

        resp = client.get(
            "/api/v1/events/historical"
            "?event_type=fed&start_date=2024-01-01&end_date=2024-06-30"
        )

        filters = resp.json()["filters"]
        assert filters["event_type"] == ["fed"]
        assert filters["start_date"] == "2024-01-01"
        assert filters["end_date"] == "2024-06-30"

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_no_filters_echoed_as_nulls(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload()

        resp = client.get("/api/v1/events/historical")
        filters = resp.json()["filters"]

        assert filters["event_type"] is None
        assert filters["start_date"] is None
        assert filters["end_date"] is None


# ============================================================
# EMPTY RESULTS
# ============================================================
class TestEventsEndpointEmptyResults:
    """Empty results are 200, not 404."""

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_empty_payload_returns_200(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload()

        resp = client.get("/api/v1/events/historical")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["events"] == []
        assert body["by_type"] == {}
        assert body["unmapped_names"] == []
        assert body["insufficient"] == []

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_insufficient_and_unmapped_populated(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload(
            events=[_row("ECB Rate Decision", 15, 1.0)],
            unmapped=["ECB Rate Decision"],
            insufficient=["gdp"],
        )

        resp = client.get("/api/v1/events/historical")
        body = resp.json()

        assert body["unmapped_names"] == ["ECB Rate Decision"]
        assert body["insufficient"] == ["gdp"]


# ============================================================
# SERVICE ERRORS
# ============================================================
class TestEventsEndpointServiceErrors:
    """The service's ValueError is converted to 422."""

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_service_value_error_returns_422(
        self, mock_fetch, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.side_effect = ValueError("bad filter")

        resp = client.get("/api/v1/events/historical")

        assert resp.status_code == 422
        body = resp.json()
        assert body["detail"]["error"] == "invalid_filter"
        assert "bad filter" in body["detail"]["message"]


# ============================================================
# CACHE BEHAVIOR
# ============================================================
class TestEventsEndpointCaching:
    """Best-effort Redis caching."""

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_cache_hit_skips_service(
        self, mock_fetch, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = _fake_service_payload(
            events=[_row("FOMC", 20, 3.0)],
        )

        resp = client.get("/api/v1/events/historical")

        assert resp.status_code == 200
        mock_fetch.assert_not_called()

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_cache_miss_calls_service_and_writes(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload(
            events=[_row("FOMC", 20, 3.0)],
        )

        client.get("/api/v1/events/historical")

        mock_fetch.assert_called_once()
        mock_write.assert_called_once()

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_cache_key_is_filter_sensitive(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload()

        client.get("/api/v1/events/historical")
        first_key = mock_read.call_args.args[0]

        client.get("/api/v1/events/historical?event_type=fed")
        second_key = mock_read.call_args.args[0]

        assert first_key != second_key

    @patch("app.api.v1.events._read_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events._write_cache", new_callable=AsyncMock)
    @patch("app.api.v1.events.fetch_historical_events", new_callable=AsyncMock)
    def test_cache_key_is_order_insensitive(
        self, mock_fetch, mock_write, mock_read, client: TestClient
    ) -> None:
        mock_read.return_value = None
        mock_fetch.return_value = _fake_service_payload()

        client.get("/api/v1/events/historical?event_type=fed&event_type=cpi")
        first_key = mock_read.call_args.args[0]

        client.get("/api/v1/events/historical?event_type=cpi&event_type=fed")
        second_key = mock_read.call_args.args[0]

        assert first_key == second_key


# ============================================================
# OPENAPI
# ============================================================
class TestEventsEndpointOpenAPI:
    """The endpoint is documented in OpenAPI."""

    def test_endpoint_in_openapi(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        assert "/api/v1/events/historical" in schema["paths"]

    def test_openapi_has_422_response(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        op = schema["paths"]["/api/v1/events/historical"]["get"]
        assert "422" in op["responses"]

    def test_openapi_parameters(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        op = schema["paths"]["/api/v1/events/historical"]["get"]
        names = sorted(p["name"] for p in op.get("parameters", []))
        assert names == ["end_date", "event_type", "start_date"]