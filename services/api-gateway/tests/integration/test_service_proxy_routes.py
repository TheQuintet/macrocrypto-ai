"""Tests for API Gateway Data Service and Alert Service proxy routes."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.v1 import service_proxy
from app.services.service_proxy import ServiceProxyError


# ============================================================================
# TEST APP
# ============================================================================


@pytest.fixture
def app():
    """Create a minimal FastAPI application using the proxy router."""
    app = FastAPI()
    app.include_router(service_proxy.router, prefix="/api/v1")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_proxy(monkeypatch):
    """Replace the module-level ServiceProxy with a mock."""
    proxy = MagicMock()
    proxy.forward = AsyncMock()

    monkeypatch.setattr(
        service_proxy,
        "proxy",
        proxy,
    )

    return proxy


def make_response(
    content=b'{"message":"ok"}',
    status_code=200,
    headers=None,
):
    """Create a mock downstream response."""
    response = MagicMock()
    response.content = content
    response.status_code = status_code
    response.headers = headers or {
        "content-type": "application/json",
    }
    return response


# ============================================================================
# DATA SERVICE ROUTES
# ============================================================================


DATA_ROUTES = [
    (
        "/api/v1/btc/price",
        "/api/v1/btc/price",
    ),
    (
        "/api/v1/btc/price/history",
        "/api/v1/btc/price/history",
    ),
    (
        "/api/v1/btc/status",
        "/api/v1/btc/status",
    ),
    (
        "/api/v1/indicators",
        "/api/v1/indicators",
    ),
    (
        "/api/v1/regimes/current",
        "/api/v1/regimes/current",
    ),
    (
        "/api/v1/regimes",
        "/api/v1/regimes",
    ),
    (
        "/api/v1/regimes/performance",
        "/api/v1/regimes/performance",
    ),
    (
        "/api/v1/regimes/btc",
        "/api/v1/regimes/btc",
    ),
    (
        "/api/v1/regimes/history/similar-periods",
        "/api/v1/regimes/history/similar-periods",
    ),
    (
        "/api/v1/regimes/42",
        "/api/v1/regimes/42",
    ),
]


@pytest.mark.parametrize(
    ("gateway_path", "expected_upstream_path"),
    DATA_ROUTES,
)
def test_data_routes_forward_to_data_service(
    client,
    mock_proxy,
    gateway_path,
    expected_upstream_path,
):
    """Every Data Service route forwards to the Data Service."""
    mock_proxy.forward.return_value = make_response()

    response = client.get(gateway_path)

    assert response.status_code == 200

    call = mock_proxy.forward.await_args

    assert call.kwargs["service"] == "data"
    assert call.kwargs["method"] == "GET"
    assert call.kwargs["path"] == expected_upstream_path
    assert call.kwargs["query_string"] == ""
    assert call.kwargs["body"] is None


# ============================================================================
# ALERT SERVICE GET ROUTES
# ============================================================================


ALERT_GET_ROUTES = [
    (
        "/api/v1/alerts/price",
        "/api/v1/alerts/price",
    ),
    (
        "/api/v1/alerts/price/123",
        "/api/v1/alerts/price/123",
    ),
    (
        "/api/v1/alerts/prediction/",
        "/api/v1/alerts/prediction/",
    ),
    (
        "/api/v1/alerts/prediction/123",
        "/api/v1/alerts/prediction/123",
    ),
    (
        "/api/v1/alerts/prediction/config/456",
        "/api/v1/alerts/prediction/config/456",
    ),
    (
        "/api/v1/macro/subscriptions/456",
        "/api/v1/macro/subscriptions/456",
    ),
    (
        "/api/v1/macro/alerts/456",
        "/api/v1/macro/alerts/456",
    ),
    (
        "/api/v1/macro/notifications/456",
        "/api/v1/macro/notifications/456",
    ),
    (
        "/api/v1/macro/events/upcoming",
        "/api/v1/macro/events/upcoming",
    ),
]


@pytest.mark.parametrize(
    ("gateway_path", "expected_upstream_path"),
    ALERT_GET_ROUTES,
)
def test_alert_get_routes_forward_to_alert_service(
    client,
    mock_proxy,
    gateway_path,
    expected_upstream_path,
):
    """Every Alert Service GET route forwards to Alert Service."""
    mock_proxy.forward.return_value = make_response()

    response = client.get(gateway_path)

    assert response.status_code == 200

    call = mock_proxy.forward.await_args

    assert call.kwargs["service"] == "alert"
    assert call.kwargs["method"] == "GET"
    assert call.kwargs["path"] == expected_upstream_path
    assert call.kwargs["body"] is None


# ============================================================================
# HTTP METHODS
# ============================================================================


@pytest.mark.parametrize(
    ("method", "path", "expected_upstream_path", "body"),
    [
        (
            "POST",
            "/api/v1/alerts/price",
            "/api/v1/alerts/price",
            b'{"threshold": 100000}',
        ),
        (
            "PUT",
            "/api/v1/alerts/price/123",
            "/api/v1/alerts/price/123",
            b'{"threshold": 110000}',
        ),
        (
            "DELETE",
            "/api/v1/alerts/price/123",
            "/api/v1/alerts/price/123",
            None,
        ),
        (
            "POST",
            "/api/v1/alerts/price/123/trigger",
            "/api/v1/alerts/price/123/trigger",
            None,
        ),
        (
            "POST",
            "/api/v1/alerts/prediction/",
            "/api/v1/alerts/prediction/",
            b'{"enabled": true}',
        ),
        (
            "PUT",
            "/api/v1/alerts/prediction/123",
            "/api/v1/alerts/prediction/123",
            b'{"enabled": false}',
        ),
        (
            "DELETE",
            "/api/v1/alerts/prediction/123",
            "/api/v1/alerts/prediction/123",
            None,
        ),
        (
            "GET",
            "/api/v1/alerts/prediction/config/456",
            "/api/v1/alerts/prediction/config/456",
            None,
        ),
        (
            "PUT",
            "/api/v1/alerts/prediction/config/456",
            "/api/v1/alerts/prediction/config/456",
            b'{"enabled": true}',
        ),
        (
            "POST",
            "/api/v1/macro/subscribe",
            "/api/v1/macro/subscribe",
            b'{"event_type": "CPI"}',
        ),
        (
            "DELETE",
            "/api/v1/macro/subscribe/456/CPI",
            "/api/v1/macro/subscribe/456/CPI",
            None,
        ),
        (
            "POST",
            "/api/v1/macro/subscribe-all/456",
            "/api/v1/macro/subscribe-all/456",
            None,
        ),
        (
            "POST",
            "/api/v1/macro/unsubscribe-all/456",
            "/api/v1/macro/unsubscribe-all/456",
            None,
        ),
        (
            "POST",
            "/api/v1/macro/alerts",
            "/api/v1/macro/alerts",
            b'{"message": "test"}',
        ),
        (
            "DELETE",
            "/api/v1/macro/alerts/789",
            "/api/v1/macro/alerts/789",
            None,
        ),
        (
            "PUT",
            "/api/v1/macro/notifications/789/read",
            "/api/v1/macro/notifications/789/read",
            None,
        ),
    ],
)
def test_alert_routes_forward_correct_method_and_body(
    client,
    mock_proxy,
    method,
    path,
    expected_upstream_path,
    body,
):
    """Alert routes preserve the HTTP method and request body."""
    mock_proxy.forward.return_value = make_response()

    response = client.request(
        method,
        path,
        content=body,
        headers=(
            {"content-type": "application/json"}
            if body
            else None
        ),
    )

    assert response.status_code == 200

    call = mock_proxy.forward.await_args

    assert call.kwargs["service"] == "alert"
    assert call.kwargs["method"] == method
    assert call.kwargs["path"] == expected_upstream_path

    if body:
        assert call.kwargs["body"] == body
    else:
        assert call.kwargs["body"] is None


# ============================================================================
# QUERY STRING
# ============================================================================


def test_query_string_is_forwarded(
    client,
    mock_proxy,
):
    """Query parameters are forwarded unchanged."""
    mock_proxy.forward.return_value = make_response()

    response = client.get(
        "/api/v1/btc/price/history"
        "?start_date=2026-01-01"
        "&end_date=2026-01-31"
        "&limit=100"
    )

    assert response.status_code == 200

    call = mock_proxy.forward.await_args

    assert call.kwargs["service"] == "data"
    assert call.kwargs["method"] == "GET"
    assert call.kwargs["path"] == "/api/v1/btc/price/history"
    assert (
        call.kwargs["query_string"]
        == "start_date=2026-01-01&end_date=2026-01-31&limit=100"
    )


# ============================================================================
# PATH PARAMETER SUBSTITUTION
# ============================================================================


@pytest.mark.parametrize(
    ("method", "path", "expected_upstream_path"),
    [
        (
            "GET",
            "/api/v1/regimes/123",
            "/api/v1/regimes/123",
        ),
        (
            "GET",
            "/api/v1/alerts/price/456",
            "/api/v1/alerts/price/456",
        ),
        (
            "POST",
            "/api/v1/alerts/price/456/trigger",
            "/api/v1/alerts/price/456/trigger",
        ),
        (
            "GET",
            "/api/v1/alerts/prediction/789",
            "/api/v1/alerts/prediction/789",
        ),
        (
            "GET",
            "/api/v1/alerts/prediction/config/111",
            "/api/v1/alerts/prediction/config/111",
        ),
        (
            "DELETE",
            "/api/v1/macro/subscribe/222/CPI",
            "/api/v1/macro/subscribe/222/CPI",
        ),
        (
            "GET",
            "/api/v1/macro/subscriptions/333",
            "/api/v1/macro/subscriptions/333",
        ),
        (
            "GET",
            "/api/v1/macro/alerts/444",
            "/api/v1/macro/alerts/444",
        ),
        (
            "GET",
            "/api/v1/macro/notifications/555",
            "/api/v1/macro/notifications/555",
        ),
    ],
)
def test_path_parameters_are_replaced(
    client,
    mock_proxy,
    method,
    path,
    expected_upstream_path,
):
    """Path parameters are substituted into the upstream path."""
    mock_proxy.forward.return_value = make_response()

    response = client.request(method, path)

    assert response.status_code == 200

    call = mock_proxy.forward.await_args

    assert call.kwargs["path"] == expected_upstream_path
    assert call.kwargs["method"] == method


# ============================================================================
# RESPONSE FORWARDING
# ============================================================================


def test_downstream_response_is_returned(
    client,
    mock_proxy,
):
    """Downstream status code, body, and normal headers are returned."""
    mock_proxy.forward.return_value = make_response(
        content=b'{"price": 105000}',
        status_code=201,
        headers={
            "content-type": "application/json",
            "x-request-id": "abc123",
        },
    )

    response = client.get("/api/v1/btc/price")

    assert response.status_code == 201
    assert response.content == b'{"price": 105000}'
    assert response.headers["content-type"] == "application/json"
    assert response.headers["x-request-id"] == "abc123"


# ============================================================================
# HOP-BY-HOP HEADERS
# ============================================================================

@pytest.mark.asyncio
async def test_hop_by_hop_response_headers_are_removed(
    mock_proxy,
    monkeypatch,
):
    """Hop-by-hop response headers are removed before creating the response."""

    mock_proxy.forward.return_value = make_response(
        headers={
            "content-type": "application/json",
            "x-request-id": "abc123",
            "content-length": "999",
            "connection": "keep-alive",
            "transfer-encoding": "chunked",
        },
    )

    captured = {}

    def mock_response(
        content=None,
        status_code=200,
        headers=None,
        **kwargs,
    ):
        captured["content"] = content
        captured["status_code"] = status_code
        captured["headers"] = headers

        return MagicMock()

    monkeypatch.setattr(
        service_proxy,
        "Response",
        mock_response,
    )

    async def receive():
        return {
            "type": "http.request",
            "body": b"",
            "more_body": False,
        }

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/btc/price",
        "raw_path": b"/api/v1/btc/price",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
        "path_params": {},
    }

    request = Request(
        scope,
        receive=receive,
    )

    await service_proxy._proxy_request(
        request=request,
        service="data",
        upstream_path="/api/v1/btc/price",
    )

    response_headers = captured["headers"]

    assert response_headers["content-type"] == "application/json"
    assert response_headers["x-request-id"] == "abc123"

    assert "content-length" not in response_headers
    assert "connection" not in response_headers
    assert "transfer-encoding" not in response_headers
# ============================================================================
# REQUEST HEADERS
# ============================================================================


def test_request_headers_are_forwarded(
    client,
    mock_proxy,
):
    """Incoming request headers are passed to ServiceProxy."""
    mock_proxy.forward.return_value = make_response()

    response = client.get(
        "/api/v1/btc/price",
        headers={
            "authorization": "Bearer test-token",
            "x-request-id": "request-123",
        },
    )

    assert response.status_code == 200

    call = mock_proxy.forward.await_args

    headers = call.kwargs["headers"]

    assert headers["authorization"] == "Bearer test-token"
    assert headers["x-request-id"] == "request-123"


# ============================================================================
# SERVICE PROXY ERRORS
# ============================================================================


def test_data_service_proxy_error_returns_502(
    client,
    mock_proxy,
):
    """Data Service proxy errors are converted to HTTP 502."""
    mock_proxy.forward.side_effect = ServiceProxyError(
        "Data Service unavailable"
    )

    response = client.get("/api/v1/btc/price")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Data Service unavailable",
    }


def test_alert_service_proxy_error_returns_502(
    client,
    mock_proxy,
):
    """Alert Service proxy errors are converted to HTTP 502."""
    mock_proxy.forward.side_effect = ServiceProxyError(
        "Alert Service unavailable"
    )

    response = client.get("/api/v1/alerts/price")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Alert Service unavailable",
    }


# ============================================================================
# ROUTE REGISTRATION
# ============================================================================


def test_all_34_proxy_routes_are_registered():
    """Exactly 34 proxy route definitions are registered."""
    routes = [
        route
        for route in service_proxy.router.routes
        if hasattr(route, "methods")
    ]

    assert len(routes) == 34


def test_data_service_route_count():
    """Exactly 10 Data Service routes are registered."""
    data_routes = [
        route
        for route in service_proxy.router.routes
        if "Data Service" in getattr(route, "tags", [])
    ]

    assert len(data_routes) == 10


def test_alert_service_route_count():
    """Exactly 24 Alert Service routes are registered."""
    alert_routes = [
        route
        for route in service_proxy.router.routes
        if "Alert Service" in getattr(route, "tags", [])
    ]

    assert len(alert_routes) == 24


# ============================================================================
# NO AUTHENTICATION REQUIREMENT
# ============================================================================


def test_proxy_routes_do_not_require_authentication(
    client,
    mock_proxy,
):
    """
    Proxy routes do not require authentication at the gateway level.
    """
    mock_proxy.forward.return_value = make_response()

    response = client.get("/api/v1/btc/price")

    assert response.status_code == 200
    mock_proxy.forward.assert_awaited_once()