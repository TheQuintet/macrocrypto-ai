import httpx
import pytest
from unittest.mock import AsyncMock, patch

from app.services.service_proxy import ServiceProxy, ServiceProxyError


@pytest.fixture
def proxy():
    return ServiceProxy(
        data_service_url="http://localhost:8001/",
        alert_service_url="http://localhost:8003/",
        ai_service_url="http://localhost:8002/",
        timeout=15.0,
    )


class TestServiceProxyInit:
    def test_strips_trailing_slashes_from_service_urls(self):
        service = ServiceProxy(
            data_service_url="http://data-service///",
            alert_service_url="http://alert-service//",
            ai_service_url="http://ai-service///",
        )

        assert service.data_service_url == "http://data-service"
        assert service.alert_service_url == "http://alert-service"
        assert service.ai_service_url == "http://ai-service"
        assert service.timeout == 30.0

    def test_accepts_custom_timeout(self):
        service = ServiceProxy(
            data_service_url="http://data-service",
            alert_service_url="http://alert-service",
            ai_service_url="http://ai-service",
            timeout=5.5,
        )

        assert service.timeout == 5.5


class TestGetBaseUrl:
    def test_returns_data_service_url(self, proxy):
        assert proxy._get_base_url("data") == "http://localhost:8001"

    def test_returns_alert_service_url(self, proxy):
        assert proxy._get_base_url("alert") == "http://localhost:8003"

    def test_returns_ai_service_url(self, proxy):
        assert proxy._get_base_url("ai") == "http://localhost:8002"

    def test_unknown_service_raises_error(self, proxy):
        with pytest.raises(
            ServiceProxyError,
            match="Unknown downstream service: unknown",
        ):
            proxy._get_base_url("unknown")


class TestForward:
    @pytest.mark.asyncio
    async def test_forwards_request_to_data_service(self, proxy):
        response = httpx.Response(
            status_code=200,
            json={"status": "ok"},
        )

        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            result = await proxy.forward(
                service="data",
                method="GET",
                path="/api/v1/btc/price",
            )

        assert result is response

        mock_request.assert_awaited_once_with(
            method="GET",
            url="http://localhost:8001/api/v1/btc/price",
            content=None,
            headers={},
        )

    @pytest.mark.asyncio
    async def test_forwards_request_to_alert_service(self, proxy):
        response = httpx.Response(
            status_code=200,
            json={"status": "ok"},
        )

        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            result = await proxy.forward(
                service="alert",
                method="GET",
                path="/api/v1/alerts",
            )

        assert result is response

        mock_request.assert_awaited_once_with(
            method="GET",
            url="http://localhost:8003/api/v1/alerts",
            content=None,
            headers={},
        )

    @pytest.mark.asyncio
    async def test_removes_leading_slashes_from_path(self, proxy):
        response = httpx.Response(status_code=200)
        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            await proxy.forward(
                service="data",
                method="GET",
                path="///api/v1/test",
            )

        mock_request.assert_awaited_once_with(
            method="GET",
            url="http://localhost:8001/api/v1/test",
            content=None,
            headers={},
        )

    @pytest.mark.asyncio
    async def test_preserves_query_string(self, proxy):
        response = httpx.Response(status_code=200)
        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            await proxy.forward(
                service="data",
                method="GET",
                path="/api/v1/btc/price",
                query_string="range=24h&interval=1h",
            )

        mock_request.assert_awaited_once_with(
            method="GET",
            url=(
                "http://localhost:8001/api/v1/btc/price"
                "?range=24h&interval=1h"
            ),
            content=None,
            headers={},
        )

    @pytest.mark.asyncio
    async def test_does_not_add_question_mark_without_query_string(self, proxy):
        response = httpx.Response(status_code=200)
        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            await proxy.forward(
                service="data",
                method="GET",
                path="/api/v1/test",
                query_string="",
            )

        mock_request.assert_awaited_once_with(
            method="GET",
            url="http://localhost:8001/api/v1/test",
            content=None,
            headers={},
        )

    @pytest.mark.asyncio
    async def test_forwards_body(self, proxy):
        response = httpx.Response(status_code=201)
        mock_request = AsyncMock(return_value=response)

        body = b'{"name":"test"}'

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            result = await proxy.forward(
                service="alert",
                method="POST",
                path="/api/v1/alerts",
                body=body,
            )

        assert result is response

        mock_request.assert_awaited_once_with(
            method="POST",
            url="http://localhost:8003/api/v1/alerts",
            content=body,
            headers={},
        )

    @pytest.mark.asyncio
    async def test_forwards_allowed_headers(self, proxy):
        response = httpx.Response(status_code=200)
        mock_request = AsyncMock(return_value=response)

        headers = {
            "Authorization": "Bearer token",
            "Content-Type": "application/json",
            "X-Request-ID": "abc123",
        }

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            await proxy.forward(
                service="data",
                method="POST",
                path="/api/v1/test",
                headers=headers,
            )

        mock_request.assert_awaited_once_with(
            method="POST",
            url="http://localhost:8001/api/v1/test",
            content=None,
            headers=headers,
        )

    @pytest.mark.asyncio
    async def test_excludes_hop_by_hop_headers_case_insensitively(self, proxy):
        response = httpx.Response(status_code=200)
        mock_request = AsyncMock(return_value=response)

        headers = {
            "Authorization": "Bearer token",
            "Host": "example.com",
            "host": "another-host",
            "Content-Length": "123",
            "CONTENT-LENGTH": "456",
            "Connection": "keep-alive",
            "connection": "close",
            "Transfer-Encoding": "chunked",
            "X-Custom": "value",
        }

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            await proxy.forward(
                service="data",
                method="GET",
                path="/api/v1/test",
                headers=headers,
            )

        forwarded_headers = mock_request.await_args.kwargs["headers"]

        assert forwarded_headers == {
            "Authorization": "Bearer token",
            "X-Custom": "value",
        }

    @pytest.mark.asyncio
    async def test_none_headers_become_empty_dict(self, proxy):
        response = httpx.Response(status_code=200)
        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            await proxy.forward(
                service="data",
                method="GET",
                path="/api/v1/test",
                headers=None,
            )

        assert mock_request.await_args.kwargs["headers"] == {}

    @pytest.mark.asyncio
    async def test_empty_headers_remain_empty_dict(self, proxy):
        response = httpx.Response(status_code=200)
        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            await proxy.forward(
                service="data",
                method="GET",
                path="/api/v1/test",
                headers={},
            )

        assert mock_request.await_args.kwargs["headers"] == {}

    @pytest.mark.asyncio
    async def test_configures_http_client_with_timeout_and_redirects(
        self,
        proxy,
    ):
        response = httpx.Response(status_code=200)
        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            await proxy.forward(
                service="data",
                method="GET",
                path="/api/v1/test",
            )

        mock_client.assert_called_once_with(
            timeout=15.0,
            follow_redirects=True,
        )

    @pytest.mark.asyncio
    async def test_returns_downstream_response_without_modification(self, proxy):
        response = httpx.Response(
            status_code=404,
            headers={"X-Test": "value"},
            content=b"not found",
        )

        mock_request = AsyncMock(return_value=response)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            result = await proxy.forward(
                service="data",
                method="GET",
                path="/api/v1/test",
            )

        assert result is response
        assert result.status_code == 404
        assert result.headers["X-Test"] == "value"
        assert result.content == b"not found"

    @pytest.mark.asyncio
    async def test_unknown_service_is_converted_to_service_proxy_error(self, proxy):
        with pytest.raises(
            ServiceProxyError,
            match="Unknown downstream service: invalid",
        ):
            await proxy.forward(
                service="invalid",
                method="GET",
                path="/api/v1/test",
            )


class TestForwardErrors:
    @pytest.mark.asyncio
    async def test_timeout_is_converted_to_service_proxy_error(self, proxy):
        timeout_error = httpx.ReadTimeout("request timed out")
        mock_request = AsyncMock(side_effect=timeout_error)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            with pytest.raises(
                ServiceProxyError,
                match="data service request timed out",
            ) as exc_info:
                await proxy.forward(
                    service="data",
                    method="GET",
                    path="/api/v1/test",
                )

        assert isinstance(exc_info.value.__cause__, httpx.TimeoutException)

    @pytest.mark.asyncio
    async def test_connect_timeout_is_converted_to_service_proxy_error(
        self,
        proxy,
    ):
        timeout_error = httpx.ConnectTimeout("connection timed out")
        mock_request = AsyncMock(side_effect=timeout_error)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            with pytest.raises(
                ServiceProxyError,
                match="alert service request timed out",
            ) as exc_info:
                await proxy.forward(
                    service="alert",
                    method="GET",
                    path="/api/v1/test",
                )

        assert isinstance(exc_info.value.__cause__, httpx.TimeoutException)

    @pytest.mark.asyncio
    async def test_request_error_is_converted_to_service_proxy_error(
        self,
        proxy,
    ):
        request_error = httpx.ConnectError("connection refused")
        mock_request = AsyncMock(side_effect=request_error)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            with pytest.raises(
                ServiceProxyError,
                match="Unable to connect to data service",
            ) as exc_info:
                await proxy.forward(
                    service="data",
                    method="GET",
                    path="/api/v1/test",
                )

        assert isinstance(exc_info.value.__cause__, httpx.RequestError)

    @pytest.mark.asyncio
    async def test_unexpected_error_is_converted_to_service_proxy_error(
        self,
        proxy,
    ):
        unexpected_error = ValueError("unexpected failure")
        mock_request = AsyncMock(side_effect=unexpected_error)

        with patch(
            "app.services.service_proxy.httpx.AsyncClient"
        ) as mock_client:
            mock_client.return_value.__aenter__.return_value.request = (
                mock_request
            )

            with pytest.raises(
                ServiceProxyError,
                match="Unexpected error calling data service",
            ) as exc_info:
                await proxy.forward(
                    service="data",
                    method="GET",
                    path="/api/v1/test",
                )

        assert isinstance(exc_info.value.__cause__, ValueError)