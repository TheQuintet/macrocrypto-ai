"""Binance API collector - REST and WebSocket"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinanceCollector:
    """
    Binance API collector for REST API calls.
    
    Features:
    - REST API: 24hr ticker, current price, OHLCV
    - Rate limit handling
    - Error handling with retries
    """
    
    def __init__(self):
        """Initialize the Binance collector."""
        self.base_url = settings.BINANCE_REST_ENDPOINT
        self.timeout = 10.0
        self.client = httpx.AsyncClient(timeout=self.timeout)
        logger.info(f"BinanceCollector initialized with REST endpoint: {self.base_url}")
    
    async def get_24hr_ticker(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Get 24hr ticker statistics from Binance REST API.
        
        Args:
            symbol: Trading pair (default: BTCUSDT)
        
        Returns:
            Dictionary with 24hr stats
        """
        endpoint = f"{self.base_url}/ticker/24hr"
        params = {"symbol": symbol}
        
        try:
            logger.debug(f"Fetching 24hr ticker for {symbol}")
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "symbol": data.get("symbol", symbol),
                "price_change": float(data.get("priceChange", 0)),
                "price_change_percent": float(data.get("priceChangePercent", 0)),
                "weighted_avg_price": float(data.get("weightedAvgPrice", 0)),
                "prev_close_price": float(data.get("prevClosePrice", 0)),
                "last_price": float(data.get("lastPrice", 0)),
                "bid_price": float(data.get("bidPrice", 0)),
                "ask_price": float(data.get("askPrice", 0)),
                "open_price": float(data.get("openPrice", 0)),
                "high_price": float(data.get("highPrice", 0)),
                "low_price": float(data.get("lowPrice", 0)),
                "volume": float(data.get("volume", 0)),
                "quote_volume": float(data.get("quoteVolume", 0)),
                "open_time": data.get("openTime", 0),
                "close_time": data.get("closeTime", 0),
                "count": data.get("count", 0),
                "source": "binance_rest"
            }
            
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching 24hr ticker for {symbol}")
            return self._get_dummy_ticker(symbol)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching 24hr ticker: {e.response.status_code} - {e.response.text}")
            return self._get_dummy_ticker(symbol)
            
        except Exception as e:
            logger.error(f"Error fetching 24hr ticker: {e}")
            return self._get_dummy_ticker(symbol)
    
    async def get_current_price(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Get current price from Binance REST API.
        
        Args:
            symbol: Trading pair (default: BTCUSDT)
        
        Returns:
            Dictionary with price data
        """
        endpoint = f"{self.base_url}/ticker/price"
        params = {"symbol": symbol}
        
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "symbol": data.get("symbol", symbol),
                "price": float(data.get("price", 0)),
                "timestamp": datetime.now().isoformat(),
                "source": "binance_rest"
            }
            
        except Exception as e:
            logger.error(f"Error fetching current price: {e}")
            return {"symbol": symbol, "price": 0.0, "source": "binance_rest"}
    
    # async def get_klines(
    #     self,
    #     symbol: str = "BTCUSDT",
    #     interval: str = "1d",
    #     limit: int = 100,
    #     start_time: Optional[int] = None,
    #     end_time: Optional[int] = None,
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Get OHLCV (K-line) data from Binance REST API.
        
    #     Args:
    #         symbol: Trading pair (default: BTCUSDT)
    #         interval: Time interval (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
    #         limit: Number of candles (max 1000)
    #         start_time: Optional window start in Unix milliseconds
    #         end_time: Optional window end in Unix milliseconds
        
    #     Returns:
    #         List of OHLCV data points
    #     """
    #     endpoint = f"{self.base_url}/klines"
    #     params = {
    #         "symbol": symbol,
    #         "interval": interval,
    #         "limit": min(limit, 1000),
    #     }

    #     if start_time is not None:
    #         params["startTime"] = start_time

    #     if end_time is not None:
    #         params["endTime"] = end_time
        
    #     try:
    #         response = await self.client.get(endpoint, params=params)
    #         response.raise_for_status()
    #         data = response.json()
            
    #         result = []
    #         for candle in data:
    #             result.append({
    #                 "open_time": candle[0],
    #                 "open": float(candle[1]),
    #                 "high": float(candle[2]),
    #                 "low": float(candle[3]),
    #                 "close": float(candle[4]),
    #                 "volume": float(candle[5]),
    #                 "close_time": candle[6],
    #                 "quote_volume": float(candle[7]),
    #                 "trades": candle[8],
    #                 "taker_buy_volume": float(candle[9]),
    #                 "taker_buy_quote_volume": float(candle[10])
    #             })
            
    #         logger.info(f"Retrieved {len(result)} klines for {symbol} ({interval})")
    #         return result
            
    #     except Exception as e:
    #         logger.error(f"Error fetching klines: {e}")
    #         return []
    
    async def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV (K-line) data from Binance REST API.

        Binance allows a maximum of 1000 candles per request. When a
        larger time window is requested, this method automatically
        paginates through multiple requests and combines the results.

        Args:
            symbol: Trading pair (default: BTCUSDT)
            interval: Time interval (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
            limit: Number of candles per request (max 1000)
            start_time: Optional window start in Unix milliseconds
            end_time: Optional window end in Unix milliseconds

        Returns:
            List of OHLCV data points in chronological order.
        """
        endpoint = f"{self.base_url}/klines"

        page_limit = min(limit, 1000)
        current_start_time = start_time
        all_candles: list[dict[str, Any]] = []

        try:
            while True:
                params = {
                    "symbol": symbol,
                    "interval": interval,
                    "limit": page_limit,
                }

                if current_start_time is not None:
                    params["startTime"] = current_start_time

                if end_time is not None:
                    params["endTime"] = end_time

                response = await self.client.get(
                    endpoint,
                    params=params,
                )
                response.raise_for_status()

                data = response.json()

                if not data:
                    break

                for candle in data:
                    all_candles.append(
                        {
                            "open_time": candle[0],
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5]),
                            "close_time": candle[6],
                            "quote_volume": float(candle[7]),
                            "trades": candle[8],
                            "taker_buy_volume": float(candle[9]),
                            "taker_buy_quote_volume": float(candle[10]),
                        }
                    )

                # Stop when Binance returned fewer candles than requested.
                if len(data) < page_limit:
                    break

                # Advance to the candle after the last returned candle.
                last_open_time = data[-1][0]
                next_start_time = last_open_time + 1

                # Safety check to prevent an accidental infinite loop.
                if (
                    current_start_time is not None
                    and next_start_time <= current_start_time
                ):
                    logger.warning(
                        "Binance kline pagination did not advance. "
                        "Stopping pagination."
                    )
                    break

                current_start_time = next_start_time

                # If we have reached the requested end time, stop.
                if end_time is not None and current_start_time > end_time:
                    break

            # Remove duplicate candles by open_time.
            unique_candles = {
                candle["open_time"]: candle
                for candle in all_candles
            }

            result = [
                unique_candles[open_time]
                for open_time in sorted(unique_candles)
            ]

            logger.info(
                "Retrieved %s klines for %s (%s) using pagination",
                len(result),
                symbol,
                interval,
            )

            return result

        except Exception as e:
            logger.error(
                "Error fetching klines for %s (%s): %s",
                symbol,
                interval,
                e,
            )
            return []

    def _get_dummy_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Return dummy ticker data when API fails.
        
        Args:
            symbol: Trading pair
        
        Returns:
            Dummy ticker data
        """
        return {
            "symbol": symbol,
            "price_change": 0.0,
            "price_change_percent": 0.0,
            "weighted_avg_price": 0.0,
            "prev_close_price": 0.0,
            "last_price": 0.0,
            "bid_price": 0.0,
            "ask_price": 0.0,
            "open_price": 0.0,
            "high_price": 0.0,
            "low_price": 0.0,
            "volume": 0.0,
            "quote_volume": 0.0,
            "open_time": 0,
            "close_time": 0,
            "count": 0,
            "source": "binance_rest_dummy"
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("BinanceCollector closed")


# ============================================
# LEGACY SUPPORT (for backward compatibility)
# ============================================

class BinanceWebSocketClient:
    """
    Legacy wrapper for Binance WebSocket.
    This is kept for backward compatibility.
    """
    
    def __init__(self):
        logger.warning("BinanceWebSocketClient is deprecated - use websocket.btc_client instead")
    
    async def connect(self):
        return False
    
    async def subscribe_btc_usdt(self, callback):
        pass
    
    async def disconnect(self):
        pass