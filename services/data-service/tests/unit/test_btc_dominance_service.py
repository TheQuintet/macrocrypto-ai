import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.btc_dominance_service import BTCDominanceService


@pytest.mark.asyncio
async def test_update_dominance():
    db = MagicMock()
    cache_client = MagicMock()

    collector = AsyncMock()
    collector.get_btc_dominance.return_value = {
        "btc_dominance": 56.42,
        "source": "coingecko",
    }

    cache_client.set = AsyncMock(return_value=True)

    record = MagicMock()
    record.dominance = 56.42
    record.time = "2026-09-10T10:00:00+00:00"
    record.source = "coingecko"

    repository = MagicMock()
    repository.create.return_value = record

    with patch(
        "app.services.btc_dominance_service.CoinGeckoCollector",
        return_value=collector,
    ), patch(
        "app.services.btc_dominance_service.BTCDominanceRepository",
        return_value=repository,
    ):
        service = BTCDominanceService(
            db=db,
            cache_client=cache_client,
        )

        result = await service.update_dominance()

    assert result is True

    collector.get_btc_dominance.assert_awaited_once()

    repository.create.assert_called_once()

    cache_client.set.assert_awaited_once()

    await service.close()


@pytest.mark.asyncio
async def test_update_dominance_invalid_value():
    db = MagicMock()
    cache_client = MagicMock()

    collector = AsyncMock()
    collector.get_btc_dominance.return_value = {
        "btc_dominance": 0.0,
        "source": "coingecko",
    }

    with patch(
        "app.services.btc_dominance_service.CoinGeckoCollector",
        return_value=collector,
    ), patch(
        "app.services.btc_dominance_service.BTCDominanceRepository",
    ):
        service = BTCDominanceService(
            db=db,
            cache_client=cache_client,
        )

        result = await service.update_dominance()

    assert result is False

    await service.close()


@pytest.mark.asyncio
async def test_get_dominance_from_cache():
    db = MagicMock()
    cache_client = MagicMock()

    cached_data = {
        "btc_dominance": 56.42,
        "time": "2026-09-10T10:00:00+00:00",
        "source": "coingecko",
    }

    cache_client.get = AsyncMock(return_value=cached_data)

    repository = MagicMock()

    with patch(
        "app.services.btc_dominance_service.BTCDominanceRepository",
        return_value=repository,
    ):
        service = BTCDominanceService(
            db=db,
            cache_client=cache_client,
        )

        result = await service.get_dominance()

    assert result == cached_data

    cache_client.get.assert_awaited_once_with(
        "btc_dominance"
    )

    repository.get_latest.assert_not_called()

    await service.close()


@pytest.mark.asyncio
async def test_get_dominance_from_database_on_cache_miss():
    db = MagicMock()
    cache_client = MagicMock()

    cache_client.get = AsyncMock(return_value=None)
    cache_client.set = AsyncMock(return_value=True)

    record = MagicMock()
    record.dominance = 56.42
    record.time = "2026-09-10T10:00:00+00:00"
    record.source = "coingecko"

    repository = MagicMock()
    repository.get_latest.return_value = record

    with patch(
        "app.services.btc_dominance_service.BTCDominanceRepository",
        return_value=repository,
    ):
        service = BTCDominanceService(
            db=db,
            cache_client=cache_client,
        )

        result = await service.get_dominance()

    assert result == {
        "btc_dominance": 56.42,
        "time": "2026-09-10T10:00:00+00:00",
        "source": "coingecko",
    }

    cache_client.get.assert_awaited_once_with(
        "btc_dominance"
    )

    repository.get_latest.assert_called_once()

    cache_client.set.assert_awaited_once()

    await service.close()


@pytest.mark.asyncio
async def test_get_dominance_returns_none_when_no_data():
    db = MagicMock()
    cache_client = MagicMock()

    cache_client.get = AsyncMock(return_value=None)

    repository = MagicMock()
    repository.get_latest.return_value = None

    with patch(
        "app.services.btc_dominance_service.BTCDominanceRepository",
        return_value=repository,
    ):
        service = BTCDominanceService(
            db=db,
            cache_client=cache_client,
        )

        result = await service.get_dominance()

    assert result is None

    cache_client.get.assert_awaited_once_with(
        "btc_dominance"
    )

    repository.get_latest.assert_called_once()

    cache_client.set.assert_not_called()

    await service.close()