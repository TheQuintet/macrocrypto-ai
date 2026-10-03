"""Data Service - FastAPI entry point for cryptocurrency and economic data collection"""

import asyncio
import sys
import logging
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI



from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi import _rate_limit_exceeded_handler

from app.config import settings
from app.database.session import init_db, engine, SessionLocal
from sqlalchemy import text
from app.cache.client import CacheClient
from app.rabbitmq.btc_update_producer import BTCUpdateProducer
from app.collectors.binance import BinanceCollector
from app.services.market_cap_service import MarketCapService
from app.services.btc_dominance_service import BTCDominanceService
# from app.collectors.fred import FREDCollector
from app.api.routes import router as api_router

# Import services
from app.services.price_service import PriceService
from app.services.history_service import HistoryService
from app.services.data_processor import DataProcessor

from app.services.scheduler import (
    periodic_macro_collection,
    periodic_economic_calendar_collection,
    periodic_regime_collection,
)

# Import rate limiting
from app.core.rate_limit import limiter


# btc_task: Optional[asyncio.Task] = None
# market_cap_task: Optional[asyncio.Task] = None
# price_service: Optional[PriceService] = None
# data_processor: Optional[DataProcessor] = None
# cache_client: Optional[CacheClient] = None
# rabbitmq_producer: Optional[RabbitMQProducer] = None
# market_cap_service: Optional[MarketCapService] = None

btc_task: Optional[asyncio.Task] = None
market_cap_task: Optional[asyncio.Task] = None
macro_task: Optional[asyncio.Task] = None
economic_task: Optional[asyncio.Task] = None
current_regime_task: Optional[asyncio.Task] = None

price_service: Optional[PriceService] = None
data_processor: Optional[DataProcessor] = None
cache_client: Optional[CacheClient] = None
rabbitmq_producer: Optional[BTCUpdateProducer] = None
market_cap_service: Optional[MarketCapService] = None
btc_dominance_service: Optional[BTCDominanceService] = None
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # global btc_task, price_service, data_processor, cache_client, rabbitmq_producer
    global btc_task, market_cap_task, economic_task, current_regime_task, price_service, data_processor, cache_client, rabbitmq_producer, market_cap_service 

    # ============================================
    # STARTUP PHASE
    # ============================================
    logger.info(f"🚀 Starting {settings.SERVICE_NAME} v{app.version}...")
    logger.info(f"📊 Log Level: {settings.LOG_LEVEL}")
    
    # --------------------------------------------
    # 1. Initialize Database
    # --------------------------------------------
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as error:
        logger.error(f"❌ Database initialization failed: {error}")
    
    # --------------------------------------------
    # 2. Connect to Redis Cache
    # --------------------------------------------
    try:
        cache_client = CacheClient()
        connected = await cache_client.connect()
        if connected:
            logger.info(f"✅ Redis cache connected at {settings.REDIS_CONNECTION_URL}")
        else:
            logger.warning("⚠️  Redis cache disabled or connection failed")
    except Exception as error:
        logger.error(f"⚠️  Redis cache connection error: {error}")
        cache_client = None
    
    # --------------------------------------------
    # 3. Connect to RabbitMQ
    # --------------------------------------------
    try:
        rabbitmq_producer = BTCUpdateProducer()
        connected = await rabbitmq_producer.connect()
        if connected:
            logger.info(f"✅ RabbitMQ connected at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
        else:
            logger.warning("⚠️  RabbitMQ connection failed")
    except Exception as error:
        logger.error(f"⚠️  RabbitMQ connection error: {error}")
        rabbitmq_producer = None
    
    # --------------------------------------------
    # 4. Initialize Price Service with Historical Data
    # --------------------------------------------
    try:
        history_service = HistoryService()
        candles = await history_service.get_daily_candles(limit=8)
        
        price_service = PriceService()
        price_service.initialize_from_history(candles)
        
        # ✅ Create DataProcessor with price_service
        data_processor = DataProcessor(price_service=price_service)
        
        logger.info(f"✅ Price service initialized with 7-day reference: {price_service.price_7d_reference}")
    except Exception as error:
        logger.warning(f"⚠️  Historical data initialization failed: {error}")
        logger.info("   (Live price updates can still continue)")
        price_service = PriceService()
        # ✅ Create DataProcessor even on error
        data_processor = DataProcessor(price_service=price_service)
    
    # ✅ Store in app state for access in routes
    app.state.price_service = price_service
    app.state.data_processor = data_processor
    app.state.cache_client = cache_client
    app.state.rabbitmq_producer = rabbitmq_producer
    
    logger.info(f"🔍 data_processor is None: {data_processor is None}")
    logger.info(f"🔍 app.state.data_processor is None: {app.state.data_processor is None}")
    
    # --------------------------------------------
    # 5. Start Real-time BTC WebSocket Stream
    # --------------------------------------------
    try:
        # ✅ Use app.state.data_processor
        btc_task = asyncio.create_task(
            run_websocket_stream(app.state.data_processor, app.state.cache_client, app.state.rabbitmq_producer)
        )
        logger.info("✅ BTC WebSocket stream started")
    except Exception as error:
        logger.error(f"❌ Failed to start BTC WebSocket stream: {error}")
        btc_task = None
    

    # --------------------------------------------
    # 6. Start BTC Market Cap Collector
    # --------------------------------------------
    try:
        if app.state.cache_client:
            market_cap_service = MarketCapService(
                app.state.cache_client
            )

            app.state.market_cap_service = market_cap_service

            market_cap_task = asyncio.create_task(
                run_market_cap_collection(
                    market_cap_service
                )
            )

            logger.info("✅ BTC market cap collector started")

        else:
            logger.warning("⚠️ Market cap collector disabled (Redis unavailable)")

    except Exception as error:
        logger.error(f"⚠️ Market cap collector startup error: {error}")
    # --------------------------------------------
   
    # --------------------------------------------
# 7. Start Periodic Data Collection Tasks
# --------------------------------------------
    try:

        asyncio.create_task(
            periodic_price_collection(
                symbol=settings.BINANCE_DEFAULT_SYMBOL,
                interval=settings.PRICE_COLLECTION_INTERVAL
            )
        )

        logger.info(
            f"✅ Periodic price collection started "
            f"(every {settings.PRICE_COLLECTION_INTERVAL}s)"
        )

        # macro_task = asyncio.create_task(
        #     periodic_macro_collection()
        # )
        macro_task = asyncio.create_task(
            periodic_macro_collection(
                cache_client=cache_client
            )
        )

        logger.info(
            "✅ Periodic macro/FRED collection started"
        )


        economic_task = asyncio.create_task(
            periodic_economic_calendar_collection()
        )

        logger.info(
            "✅ Periodic economic collection started "
            f"(daily at "
            f"{settings.MACRO_UPDATE_HOUR_UTC}:"
            f"{settings.MACRO_UPDATE_MINUTE_UTC:02d} UTC)"
        )

        current_regime_task = asyncio.create_task(
            periodic_regime_collection()
        )

        logger.info(
            "✅ Current regime scheduler started "
            f"(daily at "
            f"{settings.CURRENT_REGIME_UPDATE_HOUR_UTC}:"
            f"{settings.CURRENT_REGIME_UPDATE_MINUTE_UTC:02d} UTC)"
        )


    except Exception as error:
        logger.error(
            f"⚠️ Periodic collection startup error: {error}"
        )
    logger.info(f"✅ {settings.SERVICE_NAME} started successfully!")
    
    # ============================================
    # APPLICATION RUNS HERE
    # ============================================
    yield
    
    # ============================================
    # SHUTDOWN PHASE
    # ============================================
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}...")
    
    if btc_task:
        btc_task.cancel()
        try:
            await btc_task
            logger.info("✅ WebSocket task completed successfully")
        except asyncio.CancelledError:
            logger.info("✅ WebSocket task cancelled successfully")
        except Exception as error:
            logger.error(f"⚠️  WebSocket shutdown error: {error}")
        finally:
            btc_task = None

    if economic_task:
        economic_task.cancel()

        try:
            await economic_task

        except asyncio.CancelledError:
            logger.info(
                "✅ Economic collection task cancelled successfully"
            )

        except Exception as error:
            logger.error(
                f"⚠️ Economic shutdown error: {error}"
            )

        finally:
            economic_task = None

    if current_regime_task:
        current_regime_task.cancel()

        try:
            await current_regime_task

        except asyncio.CancelledError:
            logger.info(
                "✅ Current regime task cancelled successfully"
            )

        except Exception as error:
            logger.error(
                f"⚠️ Current regime shutdown error: {error}"
            )

        finally:
            current_regime_task = None

    
    if rabbitmq_producer:
        try:
            rabbitmq_producer.close()
            logger.info("✅ RabbitMQ connection closed")
        except Exception as error:
            logger.error(f"⚠️  RabbitMQ close error: {error}")
    
    if cache_client:
        try:
            await cache_client.close()
            logger.info("✅ Redis cache connection closed")
        except Exception as error:
            logger.error(f"⚠️  Redis close error: {error}")
    
    logger.info("✅ Shutdown complete")


async def run_websocket_stream(
    data_processor: DataProcessor,
    cache_client: Optional[CacheClient],
    rabbitmq_producer: Optional[BTCUpdateProducer]
):
    """
    Background task to run the WebSocket stream
    """
    from app.websocket.btc_client import BTCWebSocketClient
    
    logger.info(f"🔵 run_websocket_stream called with data_processor: {data_processor is not None}")
    
    if data_processor is None:
        logger.error("❌ data_processor is None! Cannot start WebSocket.")
        return
    
    logger.info(f"🔎 WebSocket DataProcessor ID: {id(data_processor)}")
    logger.info(f"🔎 WebSocket PriceService ID: {id(data_processor.price_service)}")

    # ✅ Pass rabbitmq_producer to the WebSocket client
    client = BTCWebSocketClient(
        data_processor=data_processor,
        cache_client=cache_client,
        rabbitmq_producer=rabbitmq_producer,
        on_update_callback=None
    )
    
    try:
        logger.info("🔵 Starting WebSocket client...")
        await client.start()
        logger.info("🔵 WebSocket client started, keeping alive...")
        
        # Keep the task alive
        while client.is_running:
            await asyncio.sleep(1)
        
    except asyncio.CancelledError:
        logger.info("WebSocket task cancelled")
        await client.stop()
        raise
    except Exception as error:
        logger.error(f"WebSocket task error: {error}")
        await client.stop()
        raise

async def periodic_price_collection(symbol: str = "BTCUSDT", interval: int = 60):
    """
    Periodic task to collect price data from Binance REST API
    """
    # global cache_client, rabbitmq_producer, data_processor
    
    collector = BinanceCollector()
    
    try:
        while True:
            try:
                ticker_data = await collector.get_24hr_ticker(symbol)
                
                if ticker_data:
                    # ✅ CHECK IF DATA IS VALID (not dummy)
                    price = ticker_data.get("last_price", 0.0)
                    source = ticker_data.get("source", "unknown")
                    
                    # ✅ SKIP DUMMY DATA
                    if source == "binance_rest_dummy" or price <= 0:
                        logger.warning(f"⚠️  Skipping dummy data for {symbol} (price: {price})")
                        await asyncio.sleep(interval)
                        continue
                    
                    # Process real data
                    if data_processor:
                        price_data = {
                            "symbol": symbol,
                            "price": price,
                            "open": ticker_data.get("open_price", 0.0),
                            "high": ticker_data.get("high_price", 0.0),
                            "low": ticker_data.get("low_price", 0.0),
                            "volume": ticker_data.get("volume", 0.0),
                            "quote_volume": ticker_data.get("quote_volume", 0.0),
                            "change_24h": ticker_data.get("price_change_percent", 0.0),
                            "change_abs": ticker_data.get("price_change", 0.0),
                            "source": "binance_rest",
                            "timestamp": datetime.now().isoformat()
                        }
                        data_processor.process_price_data(price_data)
                    
                    if cache_client:
                        await cache_client.set(
                            f"binance:{symbol}",
                            ticker_data,
                            ttl=interval
                        )
                    
                    # ✅ ONLY PUBLISH REAL DATA TO RABBITMQ
                    if rabbitmq_producer:
                        event_data = {
                            "symbol": symbol,
                            "price": price,
                            "open": ticker_data.get("open_price", 0.0),
                            "high": ticker_data.get("high_price", 0.0),
                            "low": ticker_data.get("low_price", 0.0),
                            "volume": ticker_data.get("volume", 0.0),
                            "quote_volume": ticker_data.get("quote_volume", 0.0),
                            "change_24h": ticker_data.get("price_change_percent", 0.0),
                            "change_abs": ticker_data.get("price_change", 0.0),
                            "source": "binance_rest",
                            "timestamp": datetime.now().isoformat()
                        }
                        rabbitmq_producer.publish_btc_update(event_data)
                    
                    logger.info(f"✅ Collected {symbol} price: ${price}")
                
            except Exception as error:
                logger.error(f"⚠️  Price collection error: {error}")
            
            await asyncio.sleep(interval)
            
    except asyncio.CancelledError:
        logger.info("Periodic price collection cancelled")
        raise
    finally:
        await collector.close()


# async def run_market_cap_collection(
#     market_cap_service: MarketCapService
# ):
#     """
#     Periodically update BTC market cap from CoinGecko.

#     Runs independently from WebSocket stream.
#     """

#     while True:
#         try:
#             updated = await market_cap_service.update_market_cap()

#             if updated:
#                 logger.info("✅ BTC market cap updated")

#             else:
#                 logger.warning("⚠️ BTC market cap update failed")

#         except Exception as error:
#             logger.error(f"⚠️ Market cap collection error: {error}")

#         # CoinGecko does not need second-by-second updates
#         await asyncio.sleep(900)

async def run_market_cap_collection(
    market_cap_service: MarketCapService,
):
    while True:
        try:
            updated = await market_cap_service.update_market_cap()

            if updated:
                logger.info("✅ BTC market cap updated")

            db = SessionLocal()

            try:
                dominance_service = BTCDominanceService(
                    db=db,
                    cache_client=cache_client,
                )

                dominance_updated = (
                    await dominance_service.update_dominance()
                )

                if dominance_updated:
                    logger.info(
                        "✅ BTC dominance updated"
                    )

                await dominance_service.close()

            finally:
                db.close()

        except Exception as error:
            logger.error(
                f"⚠️ Market data collection error: {error}"
            )

        await asyncio.sleep(900)

        
# async def periodic_economic_collection():
#     """
#     Periodically collect macroeconomic indicators from FRED
#     and update the current macroeconomic regime.

#     The process:
#     1. Waits for the configured macro update time/interval.
#     2. Creates a database session.
#     3. Updates all supported FRED indicators.
#     4. Processes macro regime detection.
#     5. Retries failed macro updates up to 3 times.
#     6. Closes the database session.
#     """

#     logger.info("🔥 FRED scheduler started")

#     from app.services.indicator_service import IndicatorService
#     from app.database.session import SessionLocal
#     from app.services.scheduler import wait_until_next_run
#     from app.config import settings

#     # Lazy import for regime processing.
#     from app.services.regime_service import RegimeService

#     while True:
#         try:
#             # ============================================
#             # WAIT FOR NEXT MACRO UPDATE
#             # ============================================

#             if settings.MACRO_UPDATE_INTERVAL_MINUTES > 0:
#                 logger.info(
#                     f"🔥 Waiting "
#                     f"{settings.MACRO_UPDATE_INTERVAL_MINUTES} minutes"
#                 )

#                 await asyncio.sleep(
#                     settings.MACRO_UPDATE_INTERVAL_MINUTES * 60
#                 )

#             else:
#                 await wait_until_next_run(
#                     settings.MACRO_UPDATE_HOUR_UTC,
#                     settings.MACRO_UPDATE_MINUTE_UTC,
#                 )

#             logger.info("🔥 FRED scheduler woke up")

#             # ============================================
#             # CREATE DATABASE SESSION
#             # ============================================

#             db = SessionLocal()

#             logger.info("🔥 Database session created")

#             try:
#                 # ========================================
#                 # UPDATE MACRO INDICATORS
#                 # ========================================

#                 service = IndicatorService(
#                     db,
#                     cache_client,
#                 )

#                 logger.info(
#                     "Starting scheduled macro update"
#                 )

#                 result = None

#                 for attempt in range(3):
#                     try:
#                         result = (
#                             await service.update_all_indicators()
#                         )

#                         logger.info(
#                             f"Macro update completed: "
#                             f"{list(result.keys())}"
#                         )

#                         break

#                     except Exception:
#                         logger.exception(
#                             f"Macro update attempt "
#                             f"{attempt + 1} failed"
#                         )

#                         if attempt == 2:
#                             raise

#                         logger.info(
#                             "Retrying macro update "
#                             "in 30 seconds..."
#                         )

#                         await asyncio.sleep(30)

#                 # ========================================
#                 # CLOSE INDICATOR SERVICE
#                 # ========================================

#                 await service.close()

#                 logger.info(
#                     "IndicatorService closed successfully"
#                 )

#                 # ========================================
#                 # UPDATE MACROECONOMIC REGIME
#                 # ========================================

#                 try:
#                     logger.info(
#                         "Starting macro regime processing"
#                     )

#                     regime_service = RegimeService(db)

#                     regime_result = (
#                         await regime_service.update_regime()
#                     )

#                     logger.info(
#                         f"Macro regime processing completed: "
#                         f"{regime_result}"
#                     )

#                     await regime_service.close()

#                 except Exception:
#                     logger.exception(
#                         "⚠️ Macro regime processing failed"
#                     )

#             finally:
#                 # ========================================
#                 # CLOSE DATABASE SESSION
#                 # ========================================

#                 db.close()

#                 logger.info(
#                     "Database session closed"
#                 )

#         except Exception:
#             logger.exception(
#                 "🔥 FRED scheduler failed"
#             )


# async def periodic_current_regime_collection():
#     """
#     Periodically process and persist the current macroeconomic regime.

#     The process:
#     1. Waits for the configured current-regime update
#        time/interval.
#     2. Creates a database session.
#     3. Loads macroeconomic indicators.
#     4. Determines the current regime.
#     5. Calculates confidence.
#     6. Determines the visual indicator.
#     7. Persists the current regime snapshot.
#     8. Closes the database session.

#     Configuration:
#         CURRENT_REGIME_UPDATE_INTERVAL_MINUTES > 0
#             Run every N minutes. Useful for QA/development.

#         CURRENT_REGIME_UPDATE_INTERVAL_MINUTES = 0
#             Use the configured daily UTC schedule.
#     """

#     logger.info("🔥 Current regime scheduler started")

#     from app.database.session import SessionLocal
#     from app.services.current_regime_service import (
#         CurrentRegimeService,
#     )
#     from app.services.scheduler import (
#         wait_until_current_regime_run,
#     )
#     from app.config import settings

#     while True:
#         try:
#             # ============================================
#             # WAIT FOR NEXT CURRENT REGIME UPDATE
#             # ============================================

#             if settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES > 0:

#                 logger.info(
#                     "🔥 Waiting "
#                     f"{settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES} "
#                     "minutes for current regime update"
#                 )

#                 await asyncio.sleep(
#                     settings.CURRENT_REGIME_UPDATE_INTERVAL_MINUTES
#                     * 60
#                 )

#             else:

#                 await wait_until_current_regime_run(
#                     settings.CURRENT_REGIME_UPDATE_HOUR_UTC,
#                     settings.CURRENT_REGIME_UPDATE_MINUTE_UTC,
#                 )

#             logger.info(
#                 "🔥 Current regime scheduler woke up"
#             )

#             # ============================================
#             # CREATE DATABASE SESSION
#             # ============================================

#             db = SessionLocal()

#             logger.info(
#                 "🔥 Current regime database session created"
#             )

#             try:
#                 # ========================================
#                 # PROCESS CURRENT REGIME
#                 # ========================================

#                 service = CurrentRegimeService(db)

#                 logger.info(
#                     "Starting current regime processing"
#                 )

#                 result = await service.process_current_regime()

#                 logger.info(
#                     "Current regime processing completed: %s",
#                     result,
#                 )

#                 await service.close()

#                 logger.info(
#                     "CurrentRegimeService closed successfully"
#                 )

#             except Exception:
#                 logger.exception(
#                     "⚠️ Current regime processing failed"
#                 )

#             finally:
#                 # ========================================
#                 # CLOSE DATABASE SESSION
#                 # ========================================

#                 db.close()

#                 logger.info(
#                     "Current regime database session closed"
#                 )

#         except asyncio.CancelledError:
#             logger.info(
#                 "Current regime scheduler cancelled"
#             )
#             raise

#         except Exception:
#             logger.exception(
#                 "🔥 Current regime scheduler failed"
#             )


# ============================================
# CREATE FASTAPI APP
# ============================================

app = FastAPI(
    title="Data Service",
    description="Collects cryptocurrency and macroeconomic data from Binance and FRED",
    version="0.1.0",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api/v1"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring"""
    # global btc_task, price_service, data_processor, cache_client, rabbitmq_producer
    
    ws_status = "unknown"
    if btc_task is None:
        ws_status = "not_started"
    elif btc_task.cancelled():
        ws_status = "cancelled"
    elif btc_task.done():
        try:
            exception = btc_task.exception()
            if exception:
                ws_status = f"error: {str(exception)}"
            else:
                ws_status = "done"
        except asyncio.CancelledError:
            ws_status = "cancelled"
        except Exception as error:
            ws_status = f"error: {str(error)}"
    else:
        ws_status = "running"
    
    db_status = "unknown"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        logger.exception("Database health check failed")
        db_status = "disconnected"
    
    dependencies = {
        "database": db_status,
        "redis": "connected" if cache_client and cache_client.is_enabled else "disabled",
        "rabbitmq": "connected" if rabbitmq_producer and rabbitmq_producer.is_connected else "disconnected",
        "price_service": "initialized" if price_service and price_service.price_7d_reference is not None else "not_initialized",
        "data_processor": "initialized" if data_processor else "not_initialized"
    }
    
    is_healthy = (
        ws_status == "running" and
        dependencies["database"] == "connected" and
        dependencies["rabbitmq"] == "connected"
    )
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": settings.SERVICE_NAME,
        "version": "0.1.0",
        "websocket": {
            "status": ws_status,
            "task_running": btc_task is not None and not btc_task.done()
        },
        "dependencies": dependencies,
        "price_7d_reference": price_service.price_7d_reference if price_service else None
    }


@app.get("/version")
async def get_version():
    """Get Python and service version information"""
    return {
        "service": settings.SERVICE_NAME,
        "service_version": "0.1.0",
        "python_version": sys.version,
        "python_version_info": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro
        },
        "environment": "production" if not settings.RELOAD else "development"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.RELOAD,
        # log_level="info",
    )