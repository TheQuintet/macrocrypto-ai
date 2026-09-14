"""AI Service — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__, __service_name__
from app.api.v1 import predict_router
from app.cache.redis_client import close_redis, ping_redis
from app.config import settings
from app.health import router as health_router
from app.scheduler.manager import scheduler_manager


# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# LIFESPAN MANAGER
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    logger.info(f"Starting {__service_name__} v{__version__}")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"Debug: {settings.debug}")

    # ============================================================
    # STARTUP
    # ============================================================
    # ---- Redis ----
    # Caching is best-effort; a failed ping logs a warning but
    # does not prevent startup.
    if await ping_redis():
        logger.info("Redis connection verified")
    else:
        logger.warning(
            "Redis is not reachable at startup. "
            "Caching will be degraded until Redis recovers."
        )

    # ---- Scheduler ----
    # Registers and starts background jobs (hourly prediction).
    # Honors settings.scheduler_enabled — a no-op in tests.
    scheduler_manager.setup()
    scheduler_manager.start()

    # Remaining startup steps (RabbitMQ consumer, MLflow,
    # model load) will be added in subsequent branches.

    yield

    # ============================================================
    # SHUTDOWN
    # ============================================================
    scheduler_manager.shutdown()
    await close_redis()
    logger.info(f"Stopping {__service_name__}")


# ============================================================
# APPLICATION
# ============================================================
app = FastAPI(
    title="MacroCrypto AI - AI Service",
    description="AI Service for Bitcoin price forecasting",
    version=__version__,
    lifespan=lifespan,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health_router, tags=["health"])
app.include_router(predict_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": __service_name__,
        "version": __version__,
        "status": "running",
        "environment": settings.environment.value,
    }