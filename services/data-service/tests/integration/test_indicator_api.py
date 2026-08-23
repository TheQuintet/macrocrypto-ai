import logging
import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app


logger = logging.getLogger(__name__)


class FakeRedisCache:
    """
    Fake Redis cache for integration tests.

    Keeps cached responses in memory between requests.
    """

    def __init__(self):
        self.storage = {}
        self.is_connected = True

    async def get(self, key):
        value = self.storage.get(key)

        if value is not None:
            logger.info("Redis HIT: %s", key)
        else:
            logger.info("Redis MISS: %s", key)

        return value

    async def set(
        self,
        key,
        value,
        ttl=None,
    ):
        self.storage[key] = value

        logger.info(
            "Redis WRITE: %s",
            key,
        )

        return True

    async def delete(self, key):
        self.storage.pop(
            key,
            None,
        )

        return True


@pytest.fixture
def client():
    """
    TestClient using an in-memory fake Redis cache.

    The fake cache is assigned after the application
    lifespan has started so the application cannot
    replace it during startup.
    """

    with TestClient(app) as client:
        fake_cache = FakeRedisCache()

        app.state.cache_client = fake_cache

        yield client


def test_get_indicators_endpoint(client):
    """
    Test successful response from the indicators endpoint.
    """

    response = client.get(
        "/api/v1/indicators"
    )

    assert response.status_code == 200

    assert response.headers[
        "content-type"
    ].startswith("application/json")

    data = response.json()

    assert "period" in data
    assert "count" in data
    assert "indicators" in data

    assert isinstance(
        data["period"],
        str,
    )

    assert isinstance(
        data["count"],
        int,
    )

    assert isinstance(
        data["indicators"],
        list,
    )

    assert data["count"] == len(
        data["indicators"]
    )


def test_indicators_response_schema(client):
    """
    Test response format and schema.
    """

    response = client.get(
        "/api/v1/indicators"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(
        data["period"],
        str,
    )

    assert isinstance(
        data["count"],
        int,
    )

    assert isinstance(
        data["indicators"],
        list,
    )

    assert len(
        data["indicators"]
    ) > 0

    for indicator in data["indicators"]:
        assert isinstance(
            indicator["indicator_name"],
            str,
        )

        assert isinstance(
            indicator["time"],
            str,
        )

        timestamp = datetime.fromisoformat(
            indicator["time"].replace(
                "Z",
                "+00:00",
            )
        )

        assert isinstance(
            timestamp,
            datetime,
        )

        assert isinstance(
            indicator["current_value"],
            (int, float),
        )

        assert (
            indicator["previous_value"] is None
            or isinstance(
                indicator["previous_value"],
                (int, float),
            )
        )

        assert (
            indicator["change_percent"] is None
            or isinstance(
                indicator["change_percent"],
                (int, float),
            )
        )

        assert indicator["trend"] in {
            "↑",
            "↓",
            "→",
        }

        assert isinstance(
            indicator["source"],
            str,
        )


@pytest.mark.parametrize(
    "period,days",
    [
        ("30d", 30),
        ("90d", 90),
        ("1y", 365),
        ("5y", 1825),
    ],
)
def test_indicators_historical_data(
    client,
    period,
    days,
):
    """
    Test historical data access for all
    supported periods.

    Verifies that returned observations fall
    within the requested historical window.
    """

    response = client.get(
        f"/api/v1/indicators?period={period}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["period"] == period

    assert isinstance(
        data["indicators"],
        list,
    )

    assert data["count"] == len(
        data["indicators"]
    )

    assert data["count"] > 0

    now = datetime.now(
        timezone.utc
    )

    start_date = (
        now - timedelta(
            days=days
        )
    )

    for indicator in data["indicators"]:
        timestamp = datetime.fromisoformat(
            indicator["time"].replace(
                "Z",
                "+00:00",
            )
        )

        assert timestamp >= start_date
        assert timestamp <= now


def test_invalid_period_returns_error(client):
    """
    Test error handling for an unsupported
    historical period.
    """

    response = client.get(
        "/api/v1/indicators?period=invalid"
    )

    assert response.status_code == 422

    data = response.json()

    assert "detail" in data


# def test_indicators_response_time(client):
#     """
#     Verify that a warm Redis cached response
#     completes in less than 500ms.

#     First request:
#         Redis MISS
#         TimescaleDB is read
#         Response is stored in Redis

#     Second request:
#         Redis HIT
#         TimescaleDB is not accessed
#     """

#     cache = app.state.cache_client

#     cache.storage.clear()

#     # ------------------------------------------
#     # First request - cold cache
#     # ------------------------------------------

#     first = client.get(
#         "/api/v1/indicators"
#     )

#     assert first.status_code == 200

#     assert (
#         "macro_indicators:latest"
#         in cache.storage
#     )

#     # ------------------------------------------
#     # Second request - warm cache
#     # ------------------------------------------

#     start = time.perf_counter()

#     response = client.get(
#         "/api/v1/indicators"
#     )

#     elapsed = (
#         time.perf_counter()
#         - start
#     )

#     assert response.status_code == 200

#     logger.info(
#         "Warm indicators response time: %.4fs",
#         elapsed,
#     )

#     assert elapsed < 0.5


def test_indicators_cache_hit_does_not_use_database(
    client,
    monkeypatch,
):
    """
    Verify that a Redis cache hit returns the
    response without creating a database session.
    """

    cache = app.state.cache_client

    cached_response = {
        "period": "30d",
        "count": 1,
        "indicators": [
            {
                "indicator_name": "test_indicator",
                "time": "2026-08-08T00:00:00+00:00",
                "current_value": 100.0,
                "previous_value": 90.0,
                "change_percent": 11.111111,
                "trend": "↑",
                "source": "test",
            }
        ],
    }

    cache.storage[
        "macro_indicators:latest"
    ] = cached_response

    def fail_database_session():
        raise AssertionError(
            "TimescaleDB was accessed despite "
            "a Redis cache hit"
        )

    monkeypatch.setattr(
        "app.api.indicators.SessionLocal",
        fail_database_session,
    )

    response = client.get(
        "/api/v1/indicators"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["period"] == "30d"
    assert data["count"] == 1

    assert (
        data["indicators"][0][
            "indicator_name"
        ]
        == "test_indicator"
    )


def test_invalid_indicator_endpoint_returns_404(
    client,
):
    """
    Test that an invalid indicators sub-route
    returns HTTP 404.
    """

    response = client.get(
        "/api/v1/indicators/invalid"
    )

    assert response.status_code == 404