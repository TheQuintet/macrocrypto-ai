import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import timezone

from app.services.indicator_service import IndicatorService


def create_service():
    return IndicatorService(MagicMock())


def test_percentage_change_calculation():
    service = create_service()
    result = service.calculate_change_percent(110, 100)
    assert result == 10


def test_percentage_change_missing_previous():
    service = create_service()
    result = service.calculate_change_percent(100, None)
    assert result is None


def test_percentage_change_previous_zero():
    service = create_service()
    result = service.calculate_change_percent(100, 0)
    assert result is None


def test_parse_fred_observations():
    service = create_service()

    response = {
        "observations": [
            {"date": "2026-01-01", "value": "100"},
            {"date": "2025-12-01", "value": "90"},
        ]
    }

    result = service.parse_observations("cpi", response)

    assert len(result) == 2
    assert result[0]["indicator_name"] == "cpi"
    assert result[0]["value"] == 100
    assert result[0]["previous_value"] == 90
    assert result[0]["change_percent"] == pytest.approx(
        11.11111111111111
    )
    assert result[0]["source"] == "fred"
    assert result[0]["time"].tzinfo == timezone.utc


def test_parse_invalid_fred_value():
    service = create_service()

    response = {
        "observations": [
            {"date": "2026-01-01", "value": "."}
        ]
    }

    result = service.parse_observations("cpi", response)

    assert result == []


def test_parse_empty_observations():
    service = create_service()

    result = service.parse_observations("cpi", {})

    assert result == []


def test_parse_invalid_observation():
    service = create_service()

    response = {
        "observations": [
            {"value": "100"}
        ]
    }

    result = service.parse_observations("cpi", response)

    assert result == []


@pytest.mark.asyncio
async def test_update_indicator_success():
    service = create_service()

    fetch_function = AsyncMock(
        return_value={
            "observations": [
                {"date": "2026-01-01", "value": "300"}
            ]
        }
    )

    service.repository.create_many = MagicMock(
        return_value=[
            {"indicator_name": "cpi", "value": 300}
        ]
    )

    result = await service.update_indicator(
        "cpi",
        fetch_function
    )

    assert len(result) == 1
    fetch_function.assert_called_once()
    service.repository.create_many.assert_called_once()


@pytest.mark.asyncio
async def test_update_indicator_no_records():
    service = create_service()

    fetch_function = AsyncMock(
        return_value={"observations": []}
    )

    service.repository.create_many = MagicMock()

    result = await service.update_indicator(
        "cpi",
        fetch_function
    )

    assert result == []
    service.repository.create_many.assert_not_called()


@pytest.mark.asyncio
async def test_update_indicator_database_error():
    service = create_service()

    fetch_function = AsyncMock(
        return_value={
            "observations": [
                {"date": "2026-01-01", "value": "300"}
            ]
        }
    )

    service.repository.create_many = MagicMock(
        side_effect=Exception("database error")
    )

    result = await service.update_indicator(
        "cpi",
        fetch_function
    )

    assert result == []


@pytest.mark.asyncio
async def test_update_indicator_fetch_error():
    service = create_service()

    fetch_function = AsyncMock(
        side_effect=Exception("fred error")
    )

    result = await service.update_indicator(
        "cpi",
        fetch_function
    )

    assert result == []


@pytest.mark.asyncio
async def test_update_all_indicators():
    service = create_service()

    empty_response = {"observations": []}

    service.collector = MagicMock()

    service.collector.get_cpi = AsyncMock(
        return_value=empty_response
    )
    service.collector.get_federal_funds_rate = AsyncMock(
        return_value=empty_response
    )
    service.collector.get_m2_money_supply = AsyncMock(
        return_value=empty_response
    )
    service.collector.get_dxy = AsyncMock(
        return_value=empty_response
    )
    service.collector.get_ten_year_treasury = AsyncMock(
        return_value=empty_response
    )
    service.collector.get_gdp = AsyncMock(
        return_value=empty_response
    )
    service.collector.get_unemployment = AsyncMock(
        return_value=empty_response
    )

    result = await service.update_all_indicators()

    assert len(result) == 8
    assert "cpi" in result
    assert "federal_funds_rate" in result
    assert "m2_money_supply" in result
    assert "dxy" in result
    assert "vix" in result
    assert "ten_year_treasury" in result
    assert "gdp" in result
    assert "unemployment" in result


@pytest.mark.asyncio
async def test_get_indicators_positive_trend():
    service = create_service()

    indicator = MagicMock()
    indicator.indicator_name = "cpi"
    indicator.time = "2026-01-01"
    indicator.value = 110
    indicator.previous_value = 100
    indicator.change_percent = 10
    indicator.source = "fred"

    service.repository.get_latest_indicators = MagicMock(
        return_value=[indicator]
    )

    result = await service.get_indicators()

    assert len(result) == 1
    assert result[0]["trend"] == "↑"


@pytest.mark.asyncio
async def test_get_indicators_negative_trend():
    service = create_service()

    indicator = MagicMock()
    indicator.indicator_name = "cpi"
    indicator.time = "2026-01-01"
    indicator.value = 90
    indicator.previous_value = 100
    indicator.change_percent = -10
    indicator.source = "fred"

    service.repository.get_latest_indicators = MagicMock(
        return_value=[indicator]
    )

    result = await service.get_indicators()

    assert result[0]["trend"] == "↓"


@pytest.mark.asyncio
async def test_get_indicators_no_change():
    service = create_service()

    indicator = MagicMock()
    indicator.indicator_name = "cpi"
    indicator.time = "2026-01-01"
    indicator.value = 100
    indicator.previous_value = 100
    indicator.change_percent = None
    indicator.source = "fred"

    service.repository.get_latest_indicators = MagicMock(
        return_value=[indicator]
    )

    result = await service.get_indicators()

    assert result[0]["trend"] == "→"


@pytest.mark.asyncio
async def test_invalidate_cache():
    service = create_service()

    service.cache_client = MagicMock()
    service.cache_client.delete = AsyncMock()

    await service.invalidate_cache()

    service.cache_client.delete.assert_any_call(
        "macro_indicators:latest"
    )


@pytest.mark.asyncio
async def test_invalidate_cache_without_client():
    service = create_service()

    service.cache_client = None

    result = await service.invalidate_cache()

    assert result is None


@pytest.mark.asyncio
async def test_close():
    service = create_service()

    service.collector = MagicMock()
    service.collector.close = AsyncMock()

    await service.close()

    service.collector.close.assert_called_once()