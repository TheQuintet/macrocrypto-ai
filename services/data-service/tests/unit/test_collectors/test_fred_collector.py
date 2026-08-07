# tests/unit/test_collectors/test_fred_collector.py

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.collectors.fred import FREDCollector


@pytest.mark.asyncio
async def test_fred_successful_api_call():
    """
    Verify that the FRED collector successfully fetches
    data from the FRED API and returns the parsed response.
    """

    collector = FREDCollector()

    mock_response_data = {
        "observations": [
            {
                "date": "2026-01-01",
                "value": "3.5"
            }
        ]
    }

    # Mock HTTP response object
    mock_response = MagicMock()

    mock_response.raise_for_status.return_value = None

    mock_response.json.return_value = (
        mock_response_data
    )

    with patch.object(
        collector.client,
        "get",
        new=AsyncMock(
            return_value=mock_response
        )
    ) as mock_get:

        result = await collector._get_series(
            "CPIAUCSL"
        )

        assert result == mock_response_data

        mock_get.assert_called_once()


    await collector.close()



@pytest.mark.asyncio
async def test_fred_timeout_handling():
    """
    Verify that timeout errors from the FRED API
    are handled gracefully.
    """

    collector = FREDCollector()

    with patch.object(
        collector.client,
        "get",
        new=AsyncMock(
            side_effect=httpx.TimeoutException(
                "timeout"
            )
        )
    ):

        result = await collector._get_series(
            "CPIAUCSL"
        )

        assert result == {}


    await collector.close()



@pytest.mark.asyncio
async def test_fred_http_error_handling():
    """
    Verify that HTTP errors from the FRED API
    are handled gracefully.
    """

    collector = FREDCollector()


    mock_response = MagicMock()

    mock_response.raise_for_status.side_effect = (
        httpx.HTTPStatusError(
            "server error",
            request=MagicMock(),
            response=httpx.Response(500)
        )
    )


    with patch.object(
        collector.client,
        "get",
        new=AsyncMock(
            return_value=mock_response
        )
    ):

        result = await collector._get_series(
            "CPIAUCSL"
        )

        assert result == {}


    await collector.close()



@pytest.mark.asyncio
async def test_fred_missing_api_key():
    """
    Verify that the collector does not call
    the FRED API when the API key is missing.
    """

    collector = FREDCollector()

    collector.api_key = None


    result = await collector._get_series(
        "CPIAUCSL"
    )


    assert result == {}


    await collector.close()