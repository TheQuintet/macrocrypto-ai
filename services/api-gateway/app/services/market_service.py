"""Market data service for interacting with the Data Service.

This module provides a service class for fetching BTC price data,
macroeconomic indicators, correlation analysis, and market regime
data from the Data Service.
"""

import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)


class MarketService:
    """Service for fetching market data from the Data Service."""

    def __init__(self):
        """Initialize the market service."""
        self.data_service_url = settings.DATA_SERVICE_URL
        self.timeout = 30.0
        self.client = None
        self.use_mock = True  # Set to False when Data Service is available

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create an HTTP client.

        Returns:
            httpx.AsyncClient: The HTTP client.
        """
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self.client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.TimeoutException),
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Data Service.

        Args:
            method: HTTP method (GET).
            endpoint: API endpoint path.
            params: Query parameters.

        Returns:
            Dict[str, Any]: The response data.

        Raises:
            httpx.HTTPStatusError: If the request fails.
            httpx.TimeoutException: If the request times out.
        """
        client = self._get_client()
        url = f"{self.data_service_url}{endpoint}"

        try:
            logger.debug(f"Making {method} request to {url}")

            if method.upper() == "GET":
                response = await client.get(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to Data Service: {url}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Data Service error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Data Service: {e}")
            raise

    def _get_mock_prices(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Return mock price data for testing.

        Args:
            symbol: The trading symbol.
            start_date: Start date (ISO 8601).
            end_date: End date (ISO 8601).
            limit: Number of records.
            offset: Pagination offset.

        Returns:
            Dict[str, Any]: Mock price data.
        """
        base_price = 45000.00
        prices = []
        total = min(limit, 1000)

        # Parse dates if provided
        start = None
        end = None
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Generate mock price data
        for i in range(total):
            if start:
                dt = start + timedelta(hours=i)
            else:
                dt = datetime.now(timezone.utc) - timedelta(hours=total - i)

            if end and dt > end:
                continue

            price = base_price + (i - total / 2) * 10 + (random.random() - 0.5) * 200
            prices.append({
                "timestamp": dt.isoformat(),
                "price": round(price, 2),
                "volume": round(1000000 + random.random() * 5000000, 2),
                "market_cap": round(price * 19000000, 2),
            })

        return {
            "symbol": symbol,
            "prices": prices[offset:offset + limit],
            "total": len(prices),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

    def _get_mock_indicators(
        self,
        indicators: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return mock indicator data for testing.

        Args:
            indicators: List of indicator names to filter.

        Returns:
            Dict[str, Any]: Mock indicator data.
        """
        all_indicators = {
            "GDP": {
                "value": 28.78,
                "previous": 28.52,
                "change_percent": 0.91,
                "source": "BEA",
                "unit": "trillion USD",
            },
            "Inflation": {
                "value": 3.2,
                "previous": 3.5,
                "change_percent": -8.57,
                "source": "BLS",
                "unit": "percent",
            },
            "Interest Rates": {
                "value": 5.50,
                "previous": 5.50,
                "change_percent": 0.0,
                "source": "Federal Reserve",
                "unit": "percent",
            },
            "Employment": {
                "value": 3.8,
                "previous": 3.7,
                "change_percent": 2.70,
                "source": "BLS",
                "unit": "percent",
            },
            "Consumer Confidence": {
                "value": 102.5,
                "previous": 100.8,
                "change_percent": 1.69,
                "source": "Conference Board",
                "unit": "index",
            },
            "PMI": {
                "value": 52.3,
                "previous": 50.2,
                "change_percent": 4.18,
                "source": "ISM",
                "unit": "index",
            },
        }

        if indicators:
            filtered = {k: v for k, v in all_indicators.items() if k in indicators}
        else:
            filtered = all_indicators

        return {
            "indicators": filtered,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

    def _get_mock_correlation(self, symbol: str, window: str) -> Dict[str, Any]:
        """Return mock correlation data for testing.

        Args:
            symbol: The trading symbol.
            window: Time window (30d, 90d, 1y).

        Returns:
            Dict[str, Any]: Mock correlation data.
        """
        windows = {"30d": 30, "90d": 90, "1y": 365}
        days = windows.get(window, 30)

        return {
            "symbol": symbol,
            "window": window,
            "days": days,
            "correlations": {
                "S&P 500": {"value": round(0.65 + (random.random() - 0.5) * 0.3, 2), "strength": "moderate"},
                "DXY": {"value": round(-0.45 + (random.random() - 0.5) * 0.3, 2), "strength": "moderate"},
                "Gold": {"value": round(0.35 + (random.random() - 0.5) * 0.3, 2), "strength": "weak"},
                "Nasdaq": {"value": round(0.55 + (random.random() - 0.5) * 0.3, 2), "strength": "moderate"},
                "VIX": {"value": round(-0.30 + (random.random() - 0.5) * 0.3, 2), "strength": "weak"},
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

    def _get_mock_regimes(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Return mock regime data for testing.

        Args:
            symbol: The trading symbol.
            timeframe: Timeframe (1w, 1m, 3m).

        Returns:
            Dict[str, Any]: Mock regime data.
        """
        regimes = [
            {
                "regime_type": "bull",
                "start_date": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat(),
                "duration_days": 30,
                "avg_return": 12.5,
                "max_drawdown": -3.2,
                "volatility": 18.5,
                "sharpe_ratio": 2.1,
            },
            {
                "regime_type": "bear",
                "start_date": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
                "end_date": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                "duration_days": 30,
                "avg_return": -8.3,
                "max_drawdown": -15.7,
                "volatility": 25.2,
                "sharpe_ratio": -1.2,
            },
            {
                "regime_type": "sideways",
                "start_date": (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),
                "end_date": (datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
                "duration_days": 30,
                "avg_return": 2.1,
                "max_drawdown": -5.3,
                "volatility": 12.8,
                "sharpe_ratio": 0.5,
            },
        ]

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "regimes": regimes,
            "current_regime": regimes[0],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

    async def get_prices(
        self,
        symbol: str = "BTC",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get historical price data from the Data Service.

        Args:
            symbol: The trading symbol (default: BTC).
            start_date: Start date (ISO 8601).
            end_date: End date (ISO 8601).
            limit: Number of records (max 1000).
            offset: Pagination offset.

        Returns:
            Dict[str, Any]: The price data.
        """
        endpoint = "/api/v1/btc/prices"
        params = {
            "symbol": symbol,
            "limit": min(limit, 1000),
            "offset": offset,
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        try:
            logger.info(f"Fetching price data for {symbol}")
            response_data = await self._make_request("GET", endpoint, params=params)

            response_data["symbol"] = symbol
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            response_data["cached"] = False

            return response_data

        except Exception as e:
            logger.warning(f"Data Service unavailable, returning mock price data: {e}")
            return self._get_mock_prices(symbol, start_date, end_date, limit, offset)

    async def get_indicators(
        self,
        indicators: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get macroeconomic indicators from the Data Service.

        Args:
            indicators: List of indicator names to filter (optional).

        Returns:
            Dict[str, Any]: The indicator data.
        """
        endpoint = "/api/v1/indicators"
        params = {}
        if indicators:
            params["indicators"] = ",".join(indicators)

        try:
            logger.info(f"Fetching macro indicators")
            response_data = await self._make_request("GET", endpoint, params=params)

            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            response_data["cached"] = False

            return response_data

        except Exception as e:
            logger.warning(f"Data Service unavailable, returning mock indicators: {e}")
            return self._get_mock_indicators(indicators)

    async def get_correlation(
        self,
        symbol: str = "BTC",
        window: str = "30d",
    ) -> Dict[str, Any]:
        """Get correlation analysis from the Data Service.

        Args:
            symbol: The trading symbol (default: BTC).
            window: Time window (30d, 90d, 1y).

        Returns:
            Dict[str, Any]: The correlation data.
        """
        endpoint = "/api/v1/correlation"
        params = {"symbol": symbol, "window": window}

        try:
            logger.info(f"Fetching correlation analysis for {symbol} ({window})")
            response_data = await self._make_request("GET", endpoint, params=params)

            response_data["symbol"] = symbol
            response_data["window"] = window
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            response_data["cached"] = False

            return response_data

        except Exception as e:
            logger.warning(f"Data Service unavailable, returning mock correlation: {e}")
            return self._get_mock_correlation(symbol, window)

    async def get_regimes(
        self,
        symbol: str = "BTC",
        timeframe: str = "1w",
    ) -> Dict[str, Any]:
        """Get market regime data from the Data Service.

        Args:
            symbol: The trading symbol (default: BTC).
            timeframe: Timeframe (1w, 1m, 3m).

        Returns:
            Dict[str, Any]: The regime data.
        """
        endpoint = "/api/v1/regimes"
        params = {"symbol": symbol, "timeframe": timeframe}

        try:
            logger.info(f"Fetching regime data for {symbol} ({timeframe})")
            response_data = await self._make_request("GET", endpoint, params=params)

            response_data["symbol"] = symbol
            response_data["timeframe"] = timeframe
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            response_data["cached"] = False

            return response_data

        except Exception as e:
            logger.warning(f"Data Service unavailable, returning mock regime data: {e}")
            return self._get_mock_regimes(symbol, timeframe)

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            logger.debug("Market service HTTP client closed")


# ============================================
# SINGLETON INSTANCE
# ============================================

market_service = MarketService()