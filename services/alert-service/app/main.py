"""Main FastAPI application for alert-service"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database.session import init_db, SessionLocal
from app.rabbitmq.btc_update_consumer import BTCUpdateConsumer
from app.rabbitmq.consumer import RabbitMQConsumer
from app.rabbitmq.producer import RabbitMQProducer
from app.api.routes import router
from app.api.prediction_routes import router as prediction_router
from app.api.macro_routes import router as macro_router
from app.api.notifications import router as notifications_router
from app.services.alert_engine import AlertEngine

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Global instances
rabbitmq_consumer = None
rabbitmq_producer = None
alert_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    global rabbitmq_consumer, rabbitmq_producer, alert_engine
    
    logger.info(f"🚀 Starting {settings.SERVICE_NAME}")
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Initialize RabbitMQ producer
    try:
        rabbitmq_producer = RabbitMQProducer()
        if rabbitmq_producer.connect():
            logger.info("✅ RabbitMQ producer connected")
        else:
            logger.warning("⚠️ RabbitMQ producer connection failed")
    except Exception as e:
        logger.error(f"❌ RabbitMQ producer initialization failed: {e}")
    
    # Initialize services
    db = SessionLocal()
    alert_engine = AlertEngine(db, rabbitmq_producer)
    logger.info("✅ Alert engine initialized")
    
    # Initialize RabbitMQ consumer with callbacks
    try:
        rabbitmq_consumer = BTCUpdateConsumer(
            RabbitMQConsumer(),
            handle_price_update,
        )
        rabbitmq_consumer.start()
        logger.info("✅ BTC price update consumer started")
    except Exception as e:
        logger.error(f"❌ RabbitMQ consumer initialization failed: {e}")
    
    logger.info(f"✅ {settings.SERVICE_NAME} started successfully")
    
    yield  # Service is running
    
    # Shutdown
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}")
    
    if rabbitmq_consumer:
        rabbitmq_consumer.close()
    if rabbitmq_producer:
        rabbitmq_producer.close()
    
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Alert Service",
    description="MacroCrypto AI Alert Service - Evaluate alerts and send notifications",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)                    # Price alerts (T7)
app.include_router(prediction_router)         # Prediction alerts (T8)
app.include_router(macro_router)              # Macro event alerts (T9)
app.include_router(notifications_router)      # Unified notifications (T10)
# ============================================
# EVENT HANDLERS
# ============================================

def handle_price_update(message: dict):
    """Handle PriceUpdated event from Data Service."""
    try:
        data = message.get("data", {})
        logger.info(f"📊 Processing price update: {data.get('symbol')} = {data.get('price')}")
        
        if not alert_engine:
            logger.warning("Alert engine not initialized")
            return
        
        # Get database session
        db = SessionLocal()
        engine = AlertEngine(db, rabbitmq_producer)
        
        # Evaluate price alerts
        triggered = engine.evaluate_price_alerts(data)
        
        if triggered:
            logger.info(f"🔔 {len(triggered)} price alerts triggered")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error handling price update: {e}")


# ============================================
# HEALTH CHECKS
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "version": "1.0.0"
    }
    
    # Check database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check RabbitMQ
    if rabbitmq_consumer and rabbitmq_consumer.is_connected:
        health_status["rabbitmq_consumer"] = "connected"
    else:
        health_status["rabbitmq_consumer"] = "disconnected"
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/ready")
async def ready_check():
    """Readiness check endpoint."""
    status = {"status": "ready"}
    
    if not (rabbitmq_consumer and rabbitmq_consumer.is_connected):
        status["status"] = "not_ready"
        status["reason"] = "RabbitMQ consumer not connected"
        return status, 503
    
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except:
        status["status"] = "not_ready"
        status["reason"] = "Database not available"
        return status, 503
    
    return status, 200


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=settings.RELOAD
    )