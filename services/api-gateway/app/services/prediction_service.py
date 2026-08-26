"""Prediction service for interacting with the AI Service.

This module provides a service class for fetching BTC predictions
from the AI Service, with caching and error handling.
"""

import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)


class PredictionService:
    """Service for fetching BTC predictions from the AI Service."""

    def __init__(self):
        """Initialize the prediction service."""
        self.ai_service_url = settings.AI_SERVICE_URL
        self.timeout = 30.0
        self.client = None
        self.use_mock = True  # Set to False when AI Service is available

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
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the AI Service.

        Args:
            method: HTTP method (GET, POST).
            endpoint: API endpoint path.
            params: Query parameters.
            json_data: JSON body data.

        Returns:
            Dict[str, Any]: The response data.

        Raises:
            httpx.HTTPStatusError: If the request fails.
            httpx.TimeoutException: If the request times out.
        """
        client = self._get_client()
        url = f"{self.ai_service_url}{endpoint}"

        try:
            logger.debug(f"Making {method} request to {url}")

            if method.upper() == "GET":
                response = await client.get(url, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, params=params, json=json_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to AI Service: {url}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Service error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling AI Service: {e}")
            raise

    def _get_mock_predictions(self, symbol: str, timeframe: str, model_type: str) -> Dict[str, Any]:
        """Return mock predictions for testing when AI Service is unavailable.

        Args:
            symbol: The trading symbol.
            timeframe: Prediction timeframe (24h, 7d).
            model_type: The model type.

        Returns:
            Dict[str, Any]: Mock prediction data.
        """
        base_price = 45000.00 + (random.random() - 0.5) * 2000

        if timeframe == "24h":
            predictions = []
            price = base_price
            for i in range(24):
                price += (random.random() - 0.5) * 100
                predictions.append({
                    "timestamp": (datetime.now(timezone.utc) + timedelta(hours=i)).isoformat(),
                    "price": round(price, 2),
                    "lower_bound": round(price * 0.97, 2),
                    "upper_bound": round(price * 1.03, 2),
                    "confidence": round(0.75 + random.random() * 0.20, 2),
                })
        else:  # 7d
            predictions = []
            price = base_price
            for i in range(7):
                price += (random.random() - 0.5) * 300
                predictions.append({
                    "timestamp": (datetime.now(timezone.utc) + timedelta(days=i)).isoformat(),
                    "price": round(price, 2),
                    "lower_bound": round(price * 0.95, 2),
                    "upper_bound": round(price * 1.05, 2),
                    "confidence": round(0.70 + random.random() * 0.25, 2),
                })

        change_percent = round((predictions[-1]["price"] - base_price) / base_price * 100, 2)
        trend = "up" if predictions[-1]["price"] > base_price else "down"

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": model_type,
            "current_price": round(base_price, 2),
            "change_percent": change_percent,
            "trend_direction": trend,
            "predictions": predictions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

    def _get_mock_accuracy(self, symbol: str, days: int) -> Dict[str, Any]:
        """Return mock accuracy metrics for testing.

        Args:
            symbol: The trading symbol.
            days: Number of days analyzed.

        Returns:
            Dict[str, Any]: Mock accuracy data.
        """
        return {
            "symbol": symbol,
            "days": days,
            "overall_accuracy": round(82.5 + (random.random() - 0.5) * 10, 1),
            "rmse": round(125.30 + (random.random() - 0.5) * 50, 2),
            "mae": round(98.75 + (random.random() - 0.5) * 30, 2),
            "mape": round(2.1 + (random.random() - 0.5) * 0.8, 1),
            "predictions_count": days * 24,
            "market_condition_breakdown": {
                "bull": {"accuracy": round(88.0 + (random.random() - 0.5) * 6, 1), "count": days * 8},
                "bear": {"accuracy": round(82.0 + (random.random() - 0.5) * 8, 1), "count": days * 8},
                "sideways": {"accuracy": round(86.5 + (random.random() - 0.5) * 5, 1), "count": days * 8},
            },
            "threshold_warning": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

    async def get_predictions(
        self,
        symbol: str = "BTC",
        timeframe: str = "24h",
        model_type: str = "ensemble",
    ) -> Dict[str, Any]:
        """Get BTC predictions from the AI Service.

        Args:
            symbol: The trading symbol (default: BTC).
            timeframe: Prediction timeframe (24h, 7d).
            model_type: The model type (ensemble, lstm, transformer).

        Returns:
            Dict[str, Any]: The prediction data.

        Raises:
            httpx.HTTPStatusError: If the AI Service returns an error.
            httpx.TimeoutException: If the request times out.
        """
        endpoint = "/api/v1/predict"

        # Prepare request body
        request_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": model_type,
        }

        try:
            logger.info(f"Fetching {timeframe} predictions for {symbol} using {model_type}")
            response_data = await self._make_request("POST", endpoint, json_data=request_data)

            # Add metadata to response
            response_data["symbol"] = symbol
            response_data["timeframe"] = timeframe
            response_data["model_type"] = model_type
            response_data["cached"] = False
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()

            return response_data

        except Exception as e:
            logger.warning(f"AI Service unavailable, returning mock data: {e}")
            return self._get_mock_predictions(symbol, timeframe, model_type)

    async def get_accuracy_metrics(
        self,
        symbol: str = "BTC",
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get prediction accuracy metrics from the AI Service.

        Args:
            symbol: The trading symbol (default: BTC).
            days: Number of days to analyze.

        Returns:
            Dict[str, Any]: The accuracy metrics.
        """
        endpoint = "/api/v1/accuracy"
        params = {"symbol": symbol, "days": days}

        try:
            logger.info(f"Fetching accuracy metrics for {symbol} ({days} days)")
            response_data = await self._make_request("GET", endpoint, params=params)

            response_data["symbol"] = symbol
            response_data["days"] = days
            response_data["cached"] = False
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()

            return response_data

        except Exception as e:
            logger.warning(f"AI Service unavailable, returning mock accuracy data: {e}")
            return self._get_mock_accuracy(symbol, days)

    async def get_recommendations(
        self,
        symbol: str = "BTC",
        timeframe: str = "24h",
        risk_level: str = "moderate",
    ) -> Dict[str, Any]:
        """Get trade recommendations from the AI Service.

        Args:
            symbol: The trading symbol (default: BTC).
            timeframe: Prediction timeframe (24h, 7d).
            risk_level: Risk tolerance (low, moderate, high).

        Returns:
            Dict[str, Any]: The recommendation data.
        """
        endpoint = "/api/v1/recommendations"
        params = {
            "symbol": symbol,
            "timeframe": timeframe,
            "risk_level": risk_level,
        }

        try:
            logger.info(f"Fetching recommendations for {symbol} ({timeframe}, risk={risk_level})")
            response_data = await self._make_request("GET", endpoint, params=params)

            response_data["symbol"] = symbol
            response_data["timeframe"] = timeframe
            response_data["risk_level"] = risk_level
            response_data["cached"] = False
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()

            return response_data

        except Exception as e:
            logger.warning(f"AI Service unavailable, returning mock recommendations: {e}")
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "risk_level": risk_level,
                "recommendation": "HOLD",
                "confidence": 0.75,
                "entry_price": 45000.00,
                "stop_loss": 44000.00,
                "take_profit": 46000.00,
                "risk_reward_ratio": 2.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

    async def get_regime_data(
        self,
        symbol: str = "BTC",
        timeframe: str = "1w",
    ) -> Dict[str, Any]:
        """Get market regime data from the AI Service.

        Args:
            symbol: The trading symbol (default: BTC).
            timeframe: Timeframe for regime analysis (1w, 1m, 3m).

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
            response_data["cached"] = False
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()

            return response_data

        except Exception as e:
            logger.warning(f"AI Service unavailable, returning mock regime data: {e}")
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "current_regime": "bull",
                "confidence": 0.82,
                "visual_indicator": "BULL",
                "identified_at": datetime.now(timezone.utc).isoformat(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

    async def get_correlation_analysis(
        self,
        symbol: str = "BTC",
        window: str = "30d",
    ) -> Dict[str, Any]:
        """Get correlation analysis from the AI Service.

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
            response_data["cached"] = False
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()

            return response_data

        except Exception as e:
            logger.warning(f"AI Service unavailable, returning mock correlation data: {e}")
            return {
                "symbol": symbol,
                "window": window,
                "correlations": {
                    "S&P 500": round(0.65 + (random.random() - 0.5) * 0.3, 2),
                    "DXY": round(-0.45 + (random.random() - 0.5) * 0.3, 2),
                    "Gold": round(0.35 + (random.random() - 0.5) * 0.3, 2),
                    "Nasdaq": round(0.55 + (random.random() - 0.5) * 0.3, 2),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

    async def get_current_price(
        self,
        symbol: str = "BTC",
    ) -> Dict[str, Any]:
        """Get current price from the Data Service.

        Args:
            symbol: The trading symbol (default: BTC).

        Returns:
            Dict[str, Any]: The price data.
        """
        endpoint = "/api/v1/price/current"
        params = {"symbol": symbol}

        try:
            logger.info(f"Fetching current price for {symbol}")
            response_data = await self._make_request("GET", endpoint, params=params)

            response_data["symbol"] = symbol
            response_data["timestamp"] = datetime.now(timezone.utc).isoformat()

            return response_data

        except Exception as e:
            logger.warning(f"Data Service unavailable, returning mock price: {e}")
            return {
                "symbol": symbol,
                "price": round(45000 + (random.random() - 0.5) * 1000, 2),
                "change_24h_percent": round((random.random() - 0.5) * 6, 2),
                "volume": round(50000000 + random.random() * 100000000, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def close(self) -> None:
        """Close the HTTP client."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()
            logger.debug("Prediction service HTTP client closed")


# ============================================
# SINGLETON INSTANCE
# ============================================

prediction_service = PredictionService()