"""API Gateway proxy routes for Data Service and Alert Service.

This module exposes the existing Data Service and Alert Service APIs through
the API Gateway.

The routes are intentionally thin forwarding routes. They contain no
business logic and delegate all downstream communication to ServiceProxy.

Source of truth:
    - 12 Data Service endpoints
    - 27 Alert Service endpoints
    - 39 proxy endpoints total
"""

from __future__ import annotations

from functools import partial
import asyncio
import websockets
from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import JSONResponse, Response

from app.core.config import settings
from app.services.service_proxy import ServiceProxy, ServiceProxyError
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter()


# ============================================================================
# SERVICE PROXY
# ============================================================================

proxy = ServiceProxy(
    data_service_url=settings.DATA_SERVICE_URL,
    alert_service_url=settings.ALERT_SERVICE_URL,
)


# ============================================================================
# GENERIC PROXY HANDLER
# ============================================================================

async def _proxy_request(
    request: Request,
    service: str,
    upstream_path: str,
) -> Response:
    """Forward a request to the appropriate downstream service."""

    body = await request.body()

    # Replace FastAPI path parameters with their actual values.
    for name, value in request.path_params.items():
        upstream_path = upstream_path.replace(
            f"{{{name}}}",
            str(value),
        )

    response = await proxy.forward(
        service=service,
        method=request.method,
        path=upstream_path,
        query_string=request.url.query,
        body=body or None,
        headers=dict(request.headers),
    )

    # Hop-by-hop headers must not be forwarded by the gateway.
    excluded_response_headers = {
        "content-length",
        "connection",
        "transfer-encoding",
    }

    response_headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in excluded_response_headers
    }

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response_headers,
    )


# ============================================================================
# DOWNSTREAM SERVICE HANDLERS
# ============================================================================

async def data_proxy(
    request: Request,
    upstream_path: str,
) -> Response:
    """Proxy a request to Data Service."""

    try:
        return await _proxy_request(
            request=request,
            service="data",
            upstream_path=upstream_path,
        )
    except ServiceProxyError as exc:
        return JSONResponse(
            status_code=502,
            content={"detail": str(exc)},
        )

async def data_websocket_proxy(
    websocket: WebSocket,
    upstream_path: str,
) -> None:
    """Proxy a WebSocket connection to Data Service."""

    await websocket.accept()

    upstream_url = (
        f"{settings.DATA_SERVICE_URL.rstrip('/')}"
        f"/{upstream_path.lstrip('/')}"
    )

    if upstream_url.startswith("http://"):
        upstream_url = "ws://" + upstream_url[len("http://"):]
    elif upstream_url.startswith("https://"):
        upstream_url = "wss://" + upstream_url[len("https://"):]

    try:
        async with websockets.connect(upstream_url) as upstream:

            async def client_to_upstream() -> None:
                while True:
                    message = await websocket.receive()

                    if message.get("text") is not None:
                        await upstream.send(message["text"])
                    elif message.get("bytes") is not None:
                        await upstream.send(message["bytes"])
                    else:
                        break

            async def upstream_to_client() -> None:
                while True:
                    message = await upstream.recv()

                    if isinstance(message, str):
                        await websocket.send_text(message)
                    else:
                        await websocket.send_bytes(message)

            await asyncio.gather(
                client_to_upstream(),
                upstream_to_client(),
            )

    except websockets.exceptions.ConnectionClosed:
        pass

    except Exception as exc:
        logger.exception(
            "WebSocket proxy error for Data Service: %s",
            exc,
        )

    finally:
        await websocket.close()

async def alert_proxy(
    request: Request,
    upstream_path: str,
) -> Response:
    """Proxy a request to Alert Service."""

    try:
        return await _proxy_request(
            request=request,
            service="alert",
            upstream_path=upstream_path,
        )
    except ServiceProxyError as exc:
        return JSONResponse(
            status_code=502,
            content={"detail": str(exc)},
        )


# ============================================================================
# DATA SERVICE — 11 ENDPOINTS
# ============================================================================

# ----------------------------------------------------------------------------
# Bitcoin — 4
# ----------------------------------------------------------------------------

router.add_api_route(
    "/btc/price",
    partial(
        data_proxy,
        upstream_path="/api/v1/btc/price",
    ),
    methods=["GET"],
    tags=["Data Service"],
)

router.add_api_route(
    "/btc/price/history",
    partial(
        data_proxy,
        upstream_path="/api/v1/btc/price/history",
    ),
    methods=["GET"],
    tags=["Data Service"],
)

router.add_api_route(
    "/btc/dominance",
    partial(
        data_proxy,
        upstream_path="/api/v1/btc/dominance",
    ),
    methods=["GET"],
    tags=["Data Service"],
)

router.add_api_websocket_route(
    "/btc/price/stream",
    partial(
        data_websocket_proxy,
        upstream_path="/api/v1/btc/price/stream",
    ),
)

router.add_api_route(
    "/btc/status",
    partial(
        data_proxy,
        upstream_path="/api/v1/btc/status",
    ),
    methods=["GET"],
    tags=["Data Service"],
)


# ----------------------------------------------------------------------------
# Indicators — 1
# ----------------------------------------------------------------------------

router.add_api_route(
    "/indicators",
    partial(
        data_proxy,
        upstream_path="/api/v1/indicators",
    ),
    methods=["GET"],
    tags=["Data Service"],
)


# ----------------------------------------------------------------------------
# Economic Calendar — 1
# ----------------------------------------------------------------------------

router.add_api_route(
    "/economic-calendar",
    partial(
        data_proxy,
        upstream_path="/api/v1/economic-calendar",
    ),
    methods=["GET"],
    tags=["Data Service"],
)


# ----------------------------------------------------------------------------
# Macroeconomic Regimes — 6
# ----------------------------------------------------------------------------

router.add_api_route(
    "/regimes/current",
    partial(
        data_proxy,
        upstream_path="/api/v1/regimes/current",
    ),
    methods=["GET"],
    tags=["Data Service"],
)

router.add_api_route(
    "/regimes",
    partial(
        data_proxy,
        upstream_path="/api/v1/regimes",
    ),
    methods=["GET"],
    tags=["Data Service"],
)

router.add_api_route(
    "/regimes/performance",
    partial(
        data_proxy,
        upstream_path="/api/v1/regimes/performance",
    ),
    methods=["GET"],
    tags=["Data Service"],
)

router.add_api_route(
    "/regimes/btc",
    partial(
        data_proxy,
        upstream_path="/api/v1/regimes/btc",
    ),
    methods=["GET"],
    tags=["Data Service"],
)

router.add_api_route(
    "/regimes/history/similar-periods",
    partial(
        data_proxy,
        upstream_path="/api/v1/regimes/history/similar-periods",
    ),
    methods=["GET"],
    tags=["Data Service"],
)

router.add_api_route(
    "/regimes/{regime_id}",
    partial(
        data_proxy,
        upstream_path="/api/v1/regimes/{regime_id}",
    ),
    methods=["GET"],
    tags=["Data Service"],
)


# ============================================================================
# ALERT SERVICE — 27 ENDPOINTS
# ============================================================================

# ----------------------------------------------------------------------------
# Price Alerts — 6
# ----------------------------------------------------------------------------

router.add_api_route(
    "/alerts/price",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/price",
    ),
    methods=["POST"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/price",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/price",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/price/{alert_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/price/{alert_id}",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/price/{alert_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/price/{alert_id}",
    ),
    methods=["PUT"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/price/{alert_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/price/{alert_id}",
    ),
    methods=["DELETE"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/price/{alert_id}/trigger",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/price/{alert_id}/trigger",
    ),
    methods=["POST"],
    tags=["Alert Service"],
)


# ----------------------------------------------------------------------------
# Prediction Alerts — 7
# ----------------------------------------------------------------------------

router.add_api_route(
    "/alerts/prediction/",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/prediction/",
    ),
    methods=["POST"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/prediction/",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/prediction/",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/prediction/{alert_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/prediction/{alert_id}",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/prediction/{alert_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/prediction/{alert_id}",
    ),
    methods=["PUT"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/prediction/{alert_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/prediction/{alert_id}",
    ),
    methods=["DELETE"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/prediction/config/{user_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/prediction/config/{user_id}",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/alerts/prediction/config/{user_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/alerts/prediction/config/{user_id}",
    ),
    methods=["PUT"],
    tags=["Alert Service"],
)


# ----------------------------------------------------------------------------
# Macro Alerts — 11
# ----------------------------------------------------------------------------

router.add_api_route(
    "/macro/subscribe",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/subscribe",
    ),
    methods=["POST"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/subscribe/{user_id}/{event_type}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/subscribe/{user_id}/{event_type}",
    ),
    methods=["DELETE"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/subscriptions/{user_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/subscriptions/{user_id}",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/subscribe-all/{user_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/subscribe-all/{user_id}",
    ),
    methods=["POST"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/unsubscribe-all/{user_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/unsubscribe-all/{user_id}",
    ),
    methods=["POST"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/alerts",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/alerts",
    ),
    methods=["POST"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/alerts/{user_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/alerts/{user_id}",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/alerts/{alert_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/alerts/{alert_id}",
    ),
    methods=["DELETE"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/notifications",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/notifications",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/notifications/unread",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/notifications/unread",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/notifications/read-all",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/notifications/read-all",
    ),
    methods=["POST"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/notifications/{user_id}",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/notifications/{user_id}",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/notifications/{notification_id}/read",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/notifications/{notification_id}/read",
    ),
    methods=["PUT"],
    tags=["Alert Service"],
)

router.add_api_route(
    "/macro/events/upcoming",
    partial(
        alert_proxy,
        upstream_path="/api/v1/macro/events/upcoming",
    ),
    methods=["GET"],
    tags=["Alert Service"],
)