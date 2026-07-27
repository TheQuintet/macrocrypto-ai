"""Data Processor - Processes incoming market data from various sources"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.services.price_service import PriceService
from app.config import settings

# Setup logging
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Handles incoming market data updates from various sources.

    Responsibilities:
    - Process raw ticker data from WebSocket/REST
    - Normalize data from different sources (Binance, Kraken, etc.)
    - Forward normalized data to PriceService
    - Handle data validation and error recovery
    - Maintain source-agnostic interface

    This is the business logic layer between data ingestion and state management.
    """

    def __init__(self, price_service: Optional[PriceService] = None):
        """
        Initialize the data processor.

        Args:
            price_service: PriceService instance for state management.
                          If None, creates a new one (for testing).
        """
        self.price_service = price_service or PriceService()
        logger.info("DataProcessor initialized")

    # ============================================
    # MAIN PROCESSING METHODS
    # ============================================

    def process_ticker_update(self, data: Dict[str, Any]) -> bool:
        """
        Process raw ticker data from WebSocket/REST.

        This is the main entry point for market data updates.

        Args:
            data: Raw ticker data from data source (Binance format expected)

        Returns:
            True if processed successfully, False otherwise

        Example:
            processor.process_ticker_update({
                "s": "BTCUSDT",
                "c": "45000.00",
                "P": "2.27",
                "h": "46000.00",
                "l": "43500.00",
                "v": "1000.00"
            })
        """
        try:
            # Validate and extract data
            price_data = self._extract_binance_data(data)

            if not price_data:
                logger.warning("Failed to extract valid price data")
                return False

            # Update price service
            self.price_service.update_price(price_data)

            logger.debug(f"Processed ticker update: {price_data['symbol']} @ ${price_data['price']}")
            return True

        except KeyError as error:
            logger.error(f"Missing required field in ticker data: {error}")
            return False

        except ValueError as error:
            logger.error(f"Invalid value in ticker data: {error}")
            return False

        except Exception as error:
            logger.error(f"Unexpected error processing ticker update: {error}")
            return False

    def process_price_data(self, price_data: Dict[str, Any]) -> bool:
        """
        Process already-normalized price data.

        Use this when data is already in standard format
        (e.g., from REST API collection).

        Args:
            price_data: Normalized price data dictionary

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            # Validate required fields
            required_fields = ['price', 'symbol']
            for field in required_fields:
                if field not in price_data:
                    logger.error(f"Missing required field: {field}")
                    return False

            # ✅ Extract and validate price
            price = float(price_data['price'])

            # ✅ SKIP DUMMY/ZERO DATA
            if price <= 0:
                logger.warning(
                    f"Skipping invalid price data: {price} for {price_data.get('symbol', 'unknown')}"
                )
                return False

            # ✅ SKIP DUMMY SOURCE
            source = price_data.get('source', 'unknown')
            if source == 'binance_rest_dummy':
                logger.warning("Skipping dummy data from REST API fallback")
                return False

            # Store validated price
            price_data['price'] = price

            # Add timestamp if not present
            if 'timestamp' not in price_data:
                price_data['timestamp'] = datetime.now(timezone.utc).isoformat()

            # ✅ Ensure all optional fields are present with defaults
            price_data['change_24h'] = float(price_data.get('change_24h', 0.0))
            price_data['change_abs'] = float(price_data.get('change_abs', 0.0))
            price_data['high'] = float(price_data.get('high', 0.0))
            price_data['low'] = float(price_data.get('low', 0.0))
            price_data['volume'] = float(price_data.get('volume', 0.0))
            price_data['open'] = float(price_data.get('open', 0.0))
            price_data['quote_volume'] = float(price_data.get('quote_volume', 0.0))
            price_data['source'] = price_data.get('source', 'unknown')

            # Update price service
            self.price_service.update_price(price_data)

            logger.debug(f"Processed price data: {price_data['symbol']} @ ${price_data['price']}")
            return True

        except ValueError as error:
            logger.error(f"Invalid value in price data: {error}")
            return False

        except Exception as error:
            logger.error(f"Unexpected error processing price data: {error}")
            return False

    def process_multiple(self, data_list: list) -> Dict[str, Any]:
        """
        Process multiple ticker updates at once.

        Args:
            data_list: List of raw ticker data

        Returns:
            Summary dict with success/failure counts
        """
        results = {
            "total": len(data_list),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for data in data_list:
            if self.process_ticker_update(data):
                results["success"] += 1
            else:
                results["failed"] += 1

        return results

    # ============================================
    # DATA EXTRACTION METHODS
    # ============================================

    def _extract_binance_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract and normalize data from Binance format.

        Args:
            data: Raw Binance ticker data

        Returns:
            Normalized price data dict or None if extraction fails

        Binance fields:
            s: Symbol
            c: Current price (close)
            o: Open price
            h: High price
            l: Low price
            v: Volume
            P: Price change percent
            p: Price change absolute
            E: Event timestamp
        """
        try:
            # Extract required fields with fallbacks
            symbol = data.get('s', settings.BINANCE_DEFAULT_SYMBOL)
            price = float(data.get('c', 0))

            if price <= 0:
                logger.warning("Invalid price value received")
                return None

            # Build normalized data structure - ALL fields extracted!
            normalized = {
                "symbol": symbol,
                "price": price,
                "open": float(data.get('o', 0)),
                "high": float(data.get('h', 0)),
                "low": float(data.get('l', 0)),
                "volume": float(data.get('v', 0)),
                "quote_volume": float(data.get('q', 0)),
                "change_24h": float(data.get('P', 0)),  # Percentage change
                "change_abs": float(data.get('p', 0)),   # Absolute change
                "timestamp": data.get('E', int(datetime.now(timezone.utc).timestamp() * 1000)),
                "source": "binance_ws"
            }

            return normalized

        except ValueError as error:
            logger.error(f"Error parsing Binance data: {error}")
            return None

    def _extract_generic_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract data from generic/unknown source.

        This attempts to find price data using common field names.

        Args:
            data: Raw data dictionary

        Returns:
            Normalized price data dict or None
        """
        try:
            # Try common field names for price
            price = None
            for field in ['price', 'last_price', 'close', 'c', 'last']:
                if field in data:
                    price = float(data[field])
                    break

            if not price or price <= 0:
                return None

            # Try common field names for other fields
            symbol = data.get('symbol', data.get('s', 'UNKNOWN'))
            high = float(data.get('high', data.get('h', 0)))
            low = float(data.get('low', data.get('l', 0)))
            volume = float(data.get('volume', data.get('v', 0)))

            normalized = {
                "symbol": symbol,
                "price": price,
                "high": high,
                "low": low,
                "volume": volume,
                "timestamp": data.get('timestamp', int(datetime.now(timezone.utc).timestamp() * 1000)),
                "source": "generic"
            }

            return normalized

        except Exception as error:
            logger.error(f"Error extracting generic data: {error}")
            return None

    # ============================================
    # UTILITY METHODS
    # ============================================

    def get_snapshot(self):
        """Get current market snapshot from PriceService."""
        return self.price_service.get_snapshot()

    def get_price(self) -> Optional[float]:
        """Get current BTC price."""
        return self.price_service.get_price()

    def is_initialized(self) -> bool:
        """Check if PriceService has valid data."""
        return self.price_service.is_initialized()

    def reset(self):
        """Reset the service state (useful for testing)."""
        self.price_service.reset()
        logger.info("DataProcessor reset")