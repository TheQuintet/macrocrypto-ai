"""AI Service — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__, __service_name__
from app.config import settings
from app.health import router as health_router


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
    # Connections (RabbitMQ, TimescaleDB, Redis, MLflow)
    # will be added in subsequent branches.
    #
    # Planned startup order:
    #   1. Connect to TimescaleDB
    #   2. Connect to Redis
    #   3. Connect to RabbitMQ
    #   4. Connect to MLflow
    #   5. Load latest model
    #   6. Start RabbitMQ consumer
    #   7. Start retraining scheduler

    yield

    # ============================================================
    # SHUTDOWN
    # ============================================================
    # Graceful shutdown of connections
    # will be added in subsequent branches.
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": __service_name__,
        "version": __version__,
        "status": "running",
        "environment": settings.environment.value,
    }