"""Mock data for testing"""

from datetime import datetime


# Sample Binance ticker data
MOCK_BINANCE_TICKER = {
    "e": "24hrTicker",
    "E": 1704787200000,
    "s": "BTCUSDT",
    "c": "45000.00",
    "o": "44000.00",
    "h": "46000.00",
    "l": "43500.00",
    "v": "1000.00",
    "q": "45000000.00",
    "P": "2.27",
    "p": "1000.00"
}

# Sample historical candles
MOCK_HISTORICAL_CANDLES = [
    {"close_price": 42000.0},
    {"close_price": 43000.0},
    {"close_price": 44000.0},
    {"close_price": 45000.0},
    {"close_price": 46000.0},
    {"close_price": 47000.0},
    {"close_price": 48000.0},
    {"close_price": 49000.0},
]

# Sample price snapshot data
MOCK_PRICE_SNAPSHOT = {
    "current_price": 45000.0,
    "change_24h": 1000.0,
    "change_24h_percent": 2.27,
    "high_24h": 46000.0,
    "low_24h": 44000.0,
    "volume_24h": 1000.0,
    "change_7d": 2000.0,
    "change_7d_percent": 4.65,
    "updated_at": datetime.now().isoformat()
}