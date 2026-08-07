import pytest
from unittest.mock import MagicMock

from app.services.data_processor import DataProcessor


@pytest.fixture
def price_service():

    service = MagicMock()

    service.get_snapshot.return_value = {
        "price": 50000
    }

    service.get_price.return_value = 50000

    service.is_initialized.return_value = True

    return service



@pytest.fixture
def processor(price_service):

    return DataProcessor(
        price_service=price_service
    )



# =====================================================
# process_ticker_update
# =====================================================


def test_process_ticker_update_success(
    processor,
    price_service
):

    data = {
        "s": "BTCUSDT",
        "c": "50000",
        "o": "49000",
        "h": "51000",
        "l": "48000",
        "v": "100",
        "P": "2",
        "p": "1000"
    }


    result = processor.process_ticker_update(
        data
    )


    assert result is True

    price_service.update_price.assert_called_once()



def test_process_ticker_update_invalid_price(
    processor
):

    result = processor.process_ticker_update(
        {
            "s": "BTCUSDT",
            "c": "0"
        }
    )


    assert result is False



def test_process_ticker_update_bad_value(
    processor
):

    result = processor.process_ticker_update(
        {
            "s": "BTCUSDT",
            "c": "invalid"
        }
    )


    assert result is False



# =====================================================
# process_price_data
# =====================================================


def test_process_price_data_success(
    processor,
    price_service
):

    data = {
        "symbol": "BTCUSDT",
        "price": "50000",
        "source": "binance_ws"
    }


    result = processor.process_price_data(
        data
    )


    assert result is True

    assert data["price"] == 50000

    price_service.update_price.assert_called_once()



def test_process_price_missing_symbol(
    processor
):

    result = processor.process_price_data(
        {
            "price": 50000
        }
    )


    assert result is False



def test_process_price_missing_price(
    processor
):

    result = processor.process_price_data(
        {
            "symbol": "BTCUSDT"
        }
    )


    assert result is False



def test_process_price_zero_price(
    processor
):

    result = processor.process_price_data(
        {
            "symbol": "BTCUSDT",
            "price": 0
        }
    )


    assert result is False



def test_process_dummy_source(
    processor
):

    result = processor.process_price_data(
        {
            "symbol": "BTCUSDT",
            "price": 50000,
            "source": "binance_rest_dummy"
        }
    )


    assert result is False



def test_process_price_invalid_value(
    processor
):

    result = processor.process_price_data(
        {
            "symbol": "BTCUSDT",
            "price": "abc"
        }
    )


    assert result is False



# =====================================================
# process_multiple
# =====================================================


def test_process_multiple(
    processor
):

    processor.process_ticker_update = MagicMock(
        side_effect=[
            True,
            False
        ]
    )


    result = processor.process_multiple(
        [
            {},
            {}
        ]
    )


    assert result["total"] == 2

    assert result["success"] == 1

    assert result["failed"] == 1



# =====================================================
# Binance extraction
# =====================================================


def test_extract_binance_data_success(
    processor
):

    result = processor._extract_binance_data(
        {
            "s": "BTCUSDT",
            "c": "50000",
            "o": "49000",
            "h": "51000",
            "l": "48000",
            "v": "100"
        }
    )


    assert result["symbol"] == "BTCUSDT"

    assert result["price"] == 50000

    assert result["source"] == "binance_ws"



def test_extract_binance_invalid_price(
    processor
):

    result = processor._extract_binance_data(
        {
            "c": "0"
        }
    )


    assert result is None



def test_extract_binance_invalid_format(
    processor
):

    result = processor._extract_binance_data(
        {
            "c": "abc"
        }
    )


    assert result is None



# =====================================================
# Generic extraction
# =====================================================


def test_extract_generic_data_price_field(
    processor
):

    result = processor._extract_generic_data(
        {
            "price": "50000",
            "symbol": "BTC"
        }
    )


    assert result["price"] == 50000

    assert result["source"] == "generic"



def test_extract_generic_last_price(
    processor
):

    result = processor._extract_generic_data(
        {
            "last_price": "50000"
        }
    )


    assert result["price"] == 50000



def test_extract_generic_invalid(
    processor
):

    result = processor._extract_generic_data(
        {
            "price": 0
        }
    )


    assert result is None



def test_extract_generic_exception(
    processor
):

    result = processor._extract_generic_data(
        {
            "price": {}
        }
    )


    assert result is None



# =====================================================
# Utility methods
# =====================================================


def test_get_snapshot(
    processor
):

    assert processor.get_snapshot() == {
        "price": 50000
    }



def test_get_price(
    processor
):

    assert processor.get_price() == 50000



def test_is_initialized(
    processor
):

    assert processor.is_initialized() is True



def test_reset(
    processor,
    price_service
):

    processor.reset()

    price_service.reset.assert_called_once()