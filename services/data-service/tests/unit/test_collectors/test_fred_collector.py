import pytest
from unittest.mock import AsyncMock

from app.collectors.fred import FREDCollector


@pytest.fixture
def fred_collector():

    collector = FREDCollector()

    collector.api_key = "test_api_key"

    return collector


# =====================================================
# _get_series tests
# =====================================================


@pytest.mark.asyncio
async def test_get_series_success(
    fred_collector
):

    fred_collector.client.get = AsyncMock()

    response = AsyncMock()

    response.raise_for_status = lambda: None

    response.json = lambda: {
        "observations": []
    }

    fred_collector.client.get.return_value = response


    result = await fred_collector._get_series(
        "GDP"
    )


    assert result == {
        "observations": []
    }


@pytest.mark.asyncio
async def test_get_series_missing_api_key(
    fred_collector
):

    fred_collector.api_key = None


    result = await fred_collector._get_series(
        "GDP"
    )


    assert result == {}


@pytest.mark.asyncio
async def test_get_series_timeout(
    fred_collector
):

    import httpx

    fred_collector.client.get = AsyncMock(
        side_effect=httpx.TimeoutException(
            "timeout"
        )
    )


    result = await fred_collector._get_series(
        "GDP"
    )


    assert result == {}


@pytest.mark.asyncio
async def test_get_series_http_error(
    fred_collector
):

    import httpx

    request = httpx.Request(
        "GET",
        "https://test.com"
    )

    response = httpx.Response(
        500,
        request=request
    )

    fred_collector.client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "error",
            request=request,
            response=response
        )
    )


    result = await fred_collector._get_series(
        "GDP"
    )


    assert result == {}


@pytest.mark.asyncio
async def test_get_series_unexpected_exception(
    fred_collector
):

    fred_collector.client.get = AsyncMock(
        side_effect=Exception(
            "unexpected error"
        )
    )


    result = await fred_collector._get_series(
        "GDP"
    )


    assert result == {}



# =====================================================
# Individual indicator methods
# =====================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method_name",
    [
        "get_cpi",
        "get_federal_funds_rate",
        "get_m2_money_supply",
        "get_dxy",
        "get_ten_year_treasury",
        "get_gdp",
        "get_unemployment",
    ],
)
async def test_indicator_methods(
    fred_collector,
    method_name
):

    fred_collector._get_series = AsyncMock(
        return_value={
            "observations": []
        }
    )


    method = getattr(
        fred_collector,
        method_name
    )


    result = await method()


    assert result == {
        "observations": []
    }


    fred_collector._get_series.assert_called_once()



# =====================================================
# get_all_indicators
# =====================================================


@pytest.mark.asyncio
async def test_get_all_indicators(
    fred_collector
):

    fred_collector.get_cpi = AsyncMock(
        return_value={}
    )

    fred_collector.get_federal_funds_rate = AsyncMock(
        return_value={}
    )

    fred_collector.get_m2_money_supply = AsyncMock(
        return_value={}
    )

    fred_collector.get_dxy = AsyncMock(
        return_value={}
    )

    fred_collector.get_ten_year_treasury = AsyncMock(
        return_value={}
    )

    fred_collector.get_gdp = AsyncMock(
        return_value={}
    )

    fred_collector.get_unemployment = AsyncMock(
        return_value={}
    )


    result = await fred_collector.get_all_indicators()


    assert len(result) == 8

    assert "cpi" in result
    assert "federal_funds_rate" in result
    assert "m2_money_supply" in result
    assert "dxy" in result
    assert "vix" in result
    assert "ten_year_treasury" in result
    assert "gdp" in result
    assert "unemployment" in result



# =====================================================
# close
# =====================================================


@pytest.mark.asyncio
async def test_close(
    fred_collector
):

    fred_collector.client.aclose = AsyncMock()


    await fred_collector.close()


    fred_collector.client.aclose.assert_called_once()