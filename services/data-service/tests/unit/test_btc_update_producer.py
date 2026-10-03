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
    instance.process_data_events = Mock()
    return instance


def test_publishes_first_price_and_only_threshold_moves(producer):
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1000})
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1050})
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1119.99})
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1120})

    assert producer.publish_price_update.call_count == 2
    assert producer.publish_price_update.call_args_list[0].args[0]["price"] == 1000
    second_event = producer.publish_price_update.call_args_list[1].args[0]
    assert second_event["price"] == 1120
    assert second_event["previous_price"] == 1000
    assert second_event["symbol"] == "BTC/USD"


def test_does_not_advance_published_price_after_publish_failure(producer):
    producer.publish_price_update.return_value = False

    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1000})

    assert producer._last_published_prices == {}


def test_processes_connection_events_even_when_price_move_is_filtered(producer):
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1000})
    producer.publish_btc_update({"symbol": "BTCUSDT", "price": 1050})

    assert producer.publish_price_update.call_count == 1
    assert producer.process_data_events.call_count == 2


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
