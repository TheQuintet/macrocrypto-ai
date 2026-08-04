"""Data Service - FastAPI entry point for cryptocurrency and economic data collection"""

import asyncio
import sys
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.config import settings
from app.database.session import init_db, engine
from app.cache.client import CacheClient
from app.rabbitmq.producer import RabbitMQProducer
from app.collectors.binance import BinanceCollector
# from app.collectors.fred import FREDCollector
from app.api.routes import router as api_router

# Import services
from app.services.price_service import PriceService
from app.services.history_service import HistoryService
from app.services.data_processor import DataProcessor

# Import rate limiting
from app.core.rate_limit import limiter

# Global references for background tasks
btc_task: Optional[asyncio.Task] = None
price_service: Optional[PriceService] = None
data_processor: Optional[DataProcessor] = None
cache_client: Optional[CacheClient] = None
rabbitmq_producer: Optional[RabbitMQProducer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global btc_task, price_service, data_processor, cache_client, rabbitmq_producer
    
    # ============================================
    # STARTUP PHASE
    # ============================================
    print(f"🚀 Starting {settings.SERVICE_NAME} v{app.version}...")
    print(f"📊 Log Level: {settings.LOG_LEVEL}")
    
    # --------------------------------------------
    # 1. Initialize Database
    # --------------------------------------------
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as error:
        print(f"❌ Database initialization failed: {error}")
    
    # --------------------------------------------
    # 2. Connect to Redis Cache
    # --------------------------------------------
    try:
        cache_client = CacheClient()
        connected = await cache_client.connect()
        if connected:
            print(f"✅ Redis cache connected at {settings.REDIS_CONNECTION_URL}")
        else:
            print("⚠️  Redis cache disabled or connection failed")
    except Exception as error:
        print(f"⚠️  Redis cache connection error: {error}")
        cache_client = None
    
    # --------------------------------------------
    # 3. Connect to RabbitMQ
    # --------------------------------------------
    try:
        rabbitmq_producer = RabbitMQProducer()
        connected = await rabbitmq_producer.connect()
        if connected:
            print(f"✅ RabbitMQ connected at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
        else:
            print("⚠️  RabbitMQ connection failed")
    except Exception as error:
        print(f"⚠️  RabbitMQ connection error: {error}")
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
        
        print(f"✅ Price service initialized with 7-day reference: {price_service.price_7d_reference}")
    except Exception as error:
        print(f"⚠️  Historical data initialization failed: {error}")
        print("   (Live price updates can still continue)")
        price_service = PriceService()
        # ✅ Create DataProcessor even on error
        data_processor = DataProcessor(price_service=price_service)
    
    # ✅ Store in app state for access in routes
    app.state.price_service = price_service
    app.state.data_processor = data_processor
    app.state.cache_client = cache_client
    app.state.rabbitmq_producer = rabbitmq_producer
    
    print(f"🔍 data_processor is None: {data_processor is None}")
    print(f"🔍 app.state.data_processor is None: {app.state.data_processor is None}")
    
    # --------------------------------------------
    # 5. Start Real-time BTC WebSocket Stream
    # --------------------------------------------
    try:
        # ✅ Use app.state.data_processor
        btc_task = asyncio.create_task(
            run_websocket_stream(app.state.data_processor, app.state.cache_client, app.state.rabbitmq_producer)
        )
        print("✅ BTC WebSocket stream started")
    except Exception as error:
        print(f"❌ Failed to start BTC WebSocket stream: {error}")
        btc_task = None
    
    # --------------------------------------------
    # 6. Start Periodic Data Collection Tasks
    # --------------------------------------------
    try:
        asyncio.create_task(
            periodic_price_collection(
                symbol=settings.BINANCE_DEFAULT_SYMBOL,
                interval=settings.PRICE_COLLECTION_INTERVAL
            )
        )
        print(f"✅ Periodic price collection started (every {settings.PRICE_COLLECTION_INTERVAL}s)")
        
        # asyncio.create_task(
        #     periodic_economic_collection(
        #         interval=settings.ECONOMIC_COLLECTION_INTERVAL
        #     )
        # )
        # print(f"✅ Periodic economic collection started (every {settings.ECONOMIC_COLLECTION_INTERVAL}s)")
        print("ℹ️  Periodic economic collection disabled (FRED integration pending)")
    except Exception as error:
        print(f"⚠️  Periodic collection startup error: {error}")
    
    print(f"✅ {settings.SERVICE_NAME} started successfully!")
    
    # ============================================
    # APPLICATION RUNS HERE
    # ============================================
    yield
    
    # ============================================
    # SHUTDOWN PHASE
    # ============================================
    print(f"🛑 Shutting down {settings.SERVICE_NAME}...")
    
    if btc_task:
        btc_task.cancel()
        try:
            await btc_task
            print("✅ WebSocket task completed successfully")
        except asyncio.CancelledError:
            print("✅ WebSocket task cancelled successfully")
        except Exception as error:
            print(f"⚠️  WebSocket shutdown error: {error}")
        finally:
            btc_task = None
    
    if rabbitmq_producer:
        try:
            rabbitmq_producer.close()
            print("✅ RabbitMQ connection closed")
        except Exception as error:
            print(f"⚠️  RabbitMQ close error: {error}")
    
    if cache_client:
        try:
            await cache_client.close()
            print("✅ Redis cache connection closed")
        except Exception as error:
            print(f"⚠️  Redis close error: {error}")
    
    print("✅ Shutdown complete")


async def run_websocket_stream(
    data_processor: DataProcessor,
    cache_client: Optional[CacheClient],
    rabbitmq_producer: Optional[RabbitMQProducer]
):
    """
    Background task to run the WebSocket stream
    """
    from app.websocket.btc_client import BTCWebSocketClient
    
    print(f"🔵 run_websocket_stream called with data_processor: {data_processor is not None}")
    
    if data_processor is None:
        print("❌ data_processor is None! Cannot start WebSocket.")
        return
    
    # ✅ Pass rabbitmq_producer to the WebSocket client
    client = BTCWebSocketClient(
        data_processor=data_processor,
        cache_client=cache_client,
        rabbitmq_producer=rabbitmq_producer,
        on_update_callback=None
    )
    
    try:
        print("🔵 Starting WebSocket client...")
        await client.start()
        print("🔵 WebSocket client started, keeping alive...")
        
        # Keep the task alive
        while client.is_running:
            await asyncio.sleep(1)
        
    except asyncio.CancelledError:
        print("WebSocket task cancelled")
        await client.stop()
        raise
    except Exception as error:
        print(f"WebSocket task error: {error}")
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
                        print(f"⚠️  Skipping dummy data for {symbol} (price: {price})")
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
                        rabbitmq_producer.publish_price_update(event_data)
                    
                    print(f"✅ Collected {symbol} price: ${price}")
                
            except Exception as error:
                print(f"⚠️  Price collection error: {error}")
            
            await asyncio.sleep(interval)
            
    except asyncio.CancelledError:
        print("Periodic price collection cancelled")
        raise
    finally:
        await collector.close()

# async def periodic_economic_collection(interval: int = 3600):
#     """
#     Periodic task to collect economic indicators from FRED
#     """
#     global cache_client, rabbitmq_producer
    
#     collector = FREDCollector()
    
#     try:
#         while True:
#             try:
#                 indicators = await collector.get_all_indicators()
                
#                 if indicators:
#                     if cache_client:
#                         for key, value in indicators.items():
#                             if value and isinstance(value, (int, float)):
#                                 await cache_client.set_economic(key, {
#                                     "value": value,
#                                     "timestamp": datetime.now().isoformat()
#                                 })
                    
#                     if rabbitmq_producer:
#                         event_data = {
#                             "indicators": indicators,
#                             "timestamp": datetime.now().isoformat()
#                         }
#                         rabbitmq_producer.publish_economic_update(event_data)
                    
#                     print(f"✅ Collected economic indicators: CPI={indicators.get('cpi')}, Inflation={indicators.get('inflation')}%")
                
#             except Exception as error:
#                 print(f"⚠️  Economic collection error: {error}")
            
#             await asyncio.sleep(interval)
            
#     except asyncio.CancelledError:
#         print("Periodic economic collection cancelled")
#         raise
#     finally:
#         await collector.close()


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
            conn.execute("SELECT 1")
            db_status = "connected"
    except Exception:
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
        reload=settings.RELOAD
    )