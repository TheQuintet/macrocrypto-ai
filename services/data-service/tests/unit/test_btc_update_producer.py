from unittest.mock import Mock

import pytest

from app.rabbitmq.btc_update_producer import BTCUpdateProducer


@pytest.fixture
def producer(monkeypatch):
    monkeypatch.setattr(
        "app.rabbitmq.btc_update_producer.settings.BTC_PRICE_RABBITMQ_THRESHOLD_USD",
        120.0,
    )
    instance = BTCUpdateProducer()
    instance.publish_price_update = Mock()
    return instance


def test_publishes_first_price_and_only_threshold_moves(producer):
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1000})
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1050})
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1119.99})
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1120})

    assert producer.publish_price_update.call_count == 2
    assert producer.publish_price_update.call_args_list[0].args[0]["price"] == 1000
    assert producer.publish_price_update.call_args_list[1].args[0]["price"] == 1120


def test_publishes_when_price_moves_down_by_threshold(producer):
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1000})
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 880})

    assert producer.publish_price_update.call_count == 2


def test_tracks_price_threshold_independently_per_symbol(producer):
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1000})
    producer.publish_btc_update({"symbol": "ETHUSDT", "price": 1000})

    assert producer.publish_price_update.call_count == 2


@pytest.mark.parametrize("price_data", [{}, {"price": "invalid"}, {"price": float("nan")}])
def test_skips_missing_or_invalid_prices(producer, price_data):
    producer.publish_btc_update(price_data)

    producer.publish_price_update.assert_not_called()
