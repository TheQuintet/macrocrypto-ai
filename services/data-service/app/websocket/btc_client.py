"""BTC WebSocket client wrapper - Adapted from monolith"""

import asyncio
import json
import logging
import websockets
from typing import Optional, Callable, Any
from datetime import datetime, timezone

from app.config import settings
from app.services.data_processor import DataProcessor
from app.database.btc_price_repository import BTCPriceRepository
from app.rabbitmq.producer import RabbitMQProducer
from app.cache.client import CacheClient

# Setup logging
logger = logging.getLogger(__name__)


BINANCE_WS_URL = settings.BINANCE_WS_URL
INITIAL_RETRY_DELAY = 1
MAX_RETRY_DELAY = 60
MAX_RETRY_ATTEMPTS = 10
CONNECTION_TIMEOUT = 30


class BTCWebSocketClient:
    """
    BTC WebSocket client with automatic reconnection.
    
    Adapted from monolith implementation with:
    - Exponential backoff
    - Graceful shutdown
    - Connection timeout handling
    - Automatic reconnect
    - Callback support for price updates
    - Cache updates for latest BTC snapshot
    - RabbitMQ publishing for real-time events
    """
    
    def __init__(
        self,
        data_processor: Optional[DataProcessor] = None,
        cache_client: Optional[CacheClient] = None,
        btc_price_repository: Optional[BTCPriceRepository] = None,
        rabbitmq_producer: Optional[RabbitMQProducer] = None,
        on_update_callback: Optional[Callable] = None
    ):
        """
        Initialize the WebSocket client
        
        Args:
            data_processor: DataProcessor for processing updates
            cache_client: Redis cache client for storing latest BTC snapshot
            btc_price_repository: Repository for storing BTC price data
            rabbitmq_producer: RabbitMQ producer for publishing events
            on_update_callback: Optional callback for price updates
        """
        self.data_processor = data_processor        
        self.cache_client = cache_client
        self.rabbitmq_producer = rabbitmq_producer
        self.btc_price_repository = btc_price_repository or BTCPriceRepository()

        self.on_update_callback = on_update_callback
        self.websocket = None
        self.is_running = False
        self.task = None
        
        # Configuration (use settings for timeout)
        self.ws_url = BINANCE_WS_URL
        self.initial_retry_delay = INITIAL_RETRY_DELAY
        self.max_retry_delay = MAX_RETRY_DELAY
        self.max_retry_attempts = MAX_RETRY_ATTEMPTS
        self.connection_timeout = CONNECTION_TIMEOUT
        self.reconnect_delay = settings.WEBSOCKET_RECONNECT_DELAY
    
    async def start(self):
        """
        Start the WebSocket connection as a background task
        """
        if self.is_running:
            logger.warning("WebSocket client already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_websocket())
        logger.info("BTC WebSocket client started")
    
    async def stop(self):
        """
        Stop the WebSocket connection gracefully
        """
        self.is_running = False
        
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
                logger.info("WebSocket task stopped gracefully")
            except asyncio.CancelledError:
                logger.info("WebSocket task cancelled")
            except Exception as error:
                logger.error(f"Error stopping WebSocket task: {error}")
        
        self.task = None
        logger.info("BTC WebSocket client stopped")
    
    async def _run_websocket(self):
        """
        Main WebSocket connection loop with reconnection logic
        """
        retry_delay = self.initial_retry_delay
        retry_count = 0
        
        while self.is_running:
            if asyncio.current_task().cancelled():
                logger.info("Task cancelled, stopping...")
                break
            
            try:
                logger.info(f"Connecting to Binance BTC stream at {self.ws_url}")
                self.websocket = await websockets.connect(
                    self.ws_url,
                    open_timeout=self.connection_timeout
                )
                
                logger.info("✅ Connected to Binance BTC stream")
                
                subscribe_msg = {
                    "method": "SUBSCRIBE",
                    "params": ["btcusdt@ticker"],
                    "id": 1
                }
                await self.websocket.send(json.dumps(subscribe_msg))
                logger.info("📤 Subscribed to btcusdt@ticker")
                retry_delay = self.initial_retry_delay
                retry_count = 0
                
                while self.is_running:
                    try:
                        if asyncio.current_task().cancelled():
                            logger.info("Task cancelled, closing connection...")
                            await self.websocket.close()
                            return
                        
                        logger.info("⏳ Waiting for Binance message")

                        message = await asyncio.wait_for(
                            self.websocket.recv(),
                            timeout=30.0
                        )

                        logger.info(f"📩 Raw Binance message: {message[:200]}")
                        
                        data = json.loads(message)
                        
                        if data.get("result") is not None:
                            logger.info(f"📥 Subscription response: {data}")
                            continue
                        
                        await self._process_message(data)
                        
                    except asyncio.TimeoutError:
                        continue
                    except websockets.ConnectionClosed:
                        logger.warning("WebSocket connection closed, reconnecting...")
                        raise
                    except json.JSONDecodeError as error:
                        logger.error(f"Error decoding JSON: {error}")
                        continue
                    except Exception as error:
                        logger.error(f"Error processing message: {error}")
                        continue
                
            except asyncio.CancelledError:
                logger.info("WebSocket task cancelled, stopping gracefully...")
                break
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting...")
                retry_count += 1
            except TimeoutError:
                logger.error(f"Connection timeout after {self.connection_timeout} seconds")
                retry_count += 1
            except Exception as error:
                logger.error(f"WebSocket error: {error}")
                retry_count += 1
            
            if retry_count >= self.max_retry_attempts:
                logger.error(f"Max retry attempts ({self.max_retry_attempts}) reached, giving up")
                break
            
            logger.info(f"Retrying in {retry_delay} seconds... (Attempt {retry_count}/{self.max_retry_attempts})")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, self.max_retry_delay)
        
        logger.info("WebSocket client stopped")
        self.is_running = False
    
    async def _process_message(self, data: dict):
        """
        Process incoming WebSocket message
        """
        logger.info("🔥 ENTERED _process_message")
        try:
            if 'c' not in data:
                logger.debug("Skipping non-ticker message")
                return
            
            symbol = data.get("s", "BTCUSDT")
            price_str = data.get("c", "0")
            price = float(price_str)

            logger.info(f"💰 BTC Price: {price}")
            
           

            if self.data_processor:
                processed = self.data_processor.process_ticker_update(data)
                if processed:
                    
                    try:
                        # --- Market Cap Section ---
                        # We attempt to enrich the stored BTC price with a market cap
                        # value fetched from the cache (Redis). This market cap is
                        # maintained elsewhere (e.g., a Coingecko poller) and stored
                        # under the key "btc_market_cap". If present, we extract
                        # the 'market_cap' field and pass it to the repository so
                        # that historical price records include market capitalization
                        # along with price and volume. If the cache is unavailable
                        # or the entry is missing, market_cap remains None.
                        market_cap = None

                        if self.cache_client and self.cache_client.is_connected:
                            try:
                                market_cap_data = await self.cache_client.get("btc_market_cap")
                                if market_cap_data:
                                    market_cap = market_cap_data.get("market_cap")
                            except Exception as error:
                                logger.warning(f"Failed to get BTC market cap: {error}")

                        self.btc_price_repository.save_price(
                            price=price,
                            volume=float(data.get("v", 0)),
                            market_cap=market_cap,
                            source="binance_ws+coingecko",
                        )

                        logger.info(f"💾 BTC price stored in TimescaleDB: {price}")

                    except Exception as error:
                        logger.error(
                            f"Failed to store BTC historical price: {error}"
                        )
                logger.info(f"Cache check: processed={processed}, cache={self.cache_client}, connected={self.cache_client.is_connected if self.cache_client else None}")
                if processed and self.cache_client and self.cache_client.is_connected:
                    try:
                        snapshot = self.data_processor.get_snapshot()

                        await self.cache_client.set(
                            "btc_price_snapshot",
                            snapshot.to_dict(),
                            ttl=5,
                        )

                        logger.debug("BTC snapshot updated in Redis")

                    except Exception as error:
                        logger.warning(f"Failed to update Redis cache: {error}")

            # ✅ PUBLISH TO RABBITMQ
            if self.rabbitmq_producer:
                try:
                    price_data = {
                        "symbol": symbol,
                        "price": price,
                        "open": float(data.get("o", 0)),
                        "high": float(data.get("h", 0)),
                        "low": float(data.get("l", 0)),
                        "volume": float(data.get("v", 0)),
                        "quote_volume": float(data.get("q", 0)),
                        "change_24h": float(data.get("P", 0)),
                        "change_abs": float(data.get("p", 0)),
                        "source": "binance_ws",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    self.rabbitmq_producer.publish_price_update(price_data)
                except Exception as e:
                    logger.error(f"Failed to publish to RabbitMQ: {e}")
                
        except KeyError as error:
            logger.error(f"Missing expected field in data: {error}")
        except ValueError as error:
            logger.error(f"Error parsing price value: {error}")
        except Exception as error:
            logger.error(f"Error processing message: {error}")
    
    @property
    def is_connected(self) -> bool:
        return (
            self.websocket is not None and 
            not self.websocket.closed and 
            self.is_running
        )
    
    @property
    def current_price(self) -> Optional[float]:
        if self.data_processor:
            return self.data_processor.get_price()
        return None


# ============================================
# LEGACY SUPPORT FUNCTIONS
# ============================================

_global_client: Optional[BTCWebSocketClient] = None


async def connect_btc_price_stream():
    global _global_client
    
    if _global_client is not None and _global_client.is_running:
        logger.info("BTC WebSocket client already running")
        return
    
    try:
        from app.services.data_processor import DataProcessor
        from app.main import data_processor as global_data_processor
        from app.cache.client import CacheClient
        from app.rabbitmq.producer import RabbitMQProducer  
        
        _global_client = BTCWebSocketClient(
            data_processor=global_data_processor,
            cache_client=CacheClient(),
            rabbitmq_producer=RabbitMQProducer(),
            on_update_callback=None
        )
        
        await _global_client.start()
        
        while _global_client.is_running:
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("WebSocket task cancelled, stopping gracefully...")
        if _global_client:
            await _global_client.stop()
        raise
    except Exception as error:
        logger.error(f"Error in WebSocket connection: {error}")
        if _global_client:
            await _global_client.stop()
        raise


async def process_btc_ticker_update(data: dict):
    # global _global_client
    
    if _global_client:
        await _global_client._process_message(data)
    else:
        logger.warning("No WebSocket client available to process update")
# ---------------------------