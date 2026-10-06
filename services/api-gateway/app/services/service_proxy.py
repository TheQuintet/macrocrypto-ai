"""HTTP proxy client for forwarding API Gateway requests to downstream services."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class ServiceProxyError(Exception):
    """Raised when a downstream service cannot be reached or queried."""


class ServiceProxy:
    """Thin HTTP client used by API Gateway proxy routes."""

    def __init__(
        self,
        data_service_url: str,
        alert_service_url: str,
        ai_service_url: str,
        timeout: float = 30.0,
    ) -> None:
        self.data_service_url = data_service_url.rstrip("/")
        self.alert_service_url = alert_service_url.rstrip("/")
        self.ai_service_url = ai_service_url.rstrip("/")
        self.timeout = timeout

    def _get_base_url(self, service: str) -> str:
        """Return the configured base URL for a downstream service."""

        if service == "data":
            return self.data_service_url

        if service == "alert":
            return self.alert_service_url
        if service == "ai":
            return self.ai_service_url

        raise ServiceProxyError(f"Unknown downstream service: {service}")

    async def forward(
        self,
        service: str,
        method: str,
        path: str,
        query_string: str = "",
        body: Optional[bytes] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Forward an HTTP request to a downstream service.

        Args:
            service: Downstream service identifier ("data", "alert", or "ai").
            method: HTTP method.
            path: Downstream API path.
            query_string: Original query string.
            body: Raw request body.
            headers: Request headers.

        Returns:
            The downstream httpx.Response.

        Raises:
            ServiceProxyError: If the downstream request fails.
        """

        base_url = self._get_base_url(service)

        # The upstream path supplied by the route is already the complete
        # downstream API path, e.g. /api/v1/btc/price.
        url = f"{base_url}/{path.lstrip('/')}"

        if query_string:
            url = f"{url}?{query_string}"

        # Do not forward hop-by-hop headers.
        excluded_headers = {
            "host",
            "content-length",
            "connection",
            "transfer-encoding",
        }

        forward_headers = {
            key: value
            for key, value in (headers or {}).items()
            if key.lower() not in excluded_headers
        }

        try:
            logger.debug(
                "Proxying %s %s request to %s",
                service,
                method,
                url,
            )

            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    content=body,
                    headers=forward_headers,
                )

            return response

        except httpx.TimeoutException as exc:
            logger.error(
                "Timeout while calling %s service: %s",
                service,
                url,
            )
            raise ServiceProxyError(
                f"{service} service request timed out"
            ) from exc

        except httpx.RequestError as exc:
            logger.error(
                "Request error while calling %s service: %s",
                service,
                exc,
            )
            raise ServiceProxyError(
                f"Unable to connect to {service} service"
            ) from exc

        except Exception as exc:
            logger.exception(
                "Unexpected error while proxying request to %s service",
                service,
            )
            raise ServiceProxyError(
                f"Unexpected error calling {service} service"
            ) from exc