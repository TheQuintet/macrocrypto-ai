"""FastAPI application entry point for API Gateway service.

This module initializes the FastAPI application, configures middleware,
sets up exception handlers, and defines the root endpoints including
health checks.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings

# ============================================
# LOGGING CONFIGURATION
# ============================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(settings.SERVICE_NAME)


# ============================================
# LIFESPAN MANAGER
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    - Startup: Log service start, initialize connections
    - Shutdown: Clean up resources, close connections
    """
    # --- STARTUP ---
    logger.info(f"🚀 Starting {settings.SERVICE_NAME} v{app.version}")
    logger.info(f"📡 Listening on port {settings.SERVICE_PORT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    logger.info(f"🔄 Reload: {settings.RELOAD}")

    # Log internal service URLs
    logger.info(f"📊 Data Service: {settings.DATA_SERVICE_URL}")
    logger.info(f"🤖 AI Service: {settings.AI_SERVICE_URL}")
    logger.info(f"🔔 Alert Service: {settings.ALERT_SERVICE_URL}")

    # Log Redis status
    if settings.REDIS_ENABLED:
        logger.info(f"🗄️  Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    else:
        logger.warning("⚠️ Redis is disabled")

    logger.info(f"✅ {settings.SERVICE_NAME} started successfully")

    yield  # Application runs here

    # --- SHUTDOWN ---
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}...")


# ============================================
# CREATE FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title=settings.SERVICE_NAME,
    version="1.0.0",
    description="""
    ## API Gateway for MacroCrypto AI

    This service provides REST API endpoints for BTC Traders, Investment Analysts,
    and Platform Users.

    ### Features:
    - **Authentication**: JWT-based authentication with access/refresh tokens
    - **Predictions**: BTC price predictions from multiple AI models
    - **Market Data**: Real-time and historical market data
    - **Alerts**: Price, prediction, and macro event alerts
    - **Exports**: Data export in CSV, PNG, and PDF formats
    - **WebSocket**: Real-time price updates

    ### Rate Limits:
    - Guest: 10 requests per minute
    - User: 100 requests per minute
    - Admin: 1000 requests per minute

    ### Authentication:
    Use `/api/v1/auth/login` to get an access token.
    Include the token in the `Authorization: Bearer <token>` header.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================
# MIDDLEWARE
# ============================================

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# --- Trusted Host Middleware ---
# Disable in test environment to prevent "Invalid host header" errors
if not settings.DEBUG and not os.getenv("TESTING"):
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.macrocrypto.ai", "localhost", "127.0.0.1"],
    )


# ============================================
# EXCEPTION HANDLERS
# ============================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with detailed messages.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions.
    """
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
            "message": str(exc) if settings.DEBUG else None,
        },
    )


# ============================================
# REQUEST LOGGING MIDDLEWARE (Optional)
# ============================================

# Uncomment this middleware to log all incoming requests
# from starlette.middleware.base import BaseHTTPMiddleware
# from time import time
#
# class LoggingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         start_time = time()
#         response = await call_next(request)
#         duration = (time() - start_time) * 1000
#         logger.info(
#             f"{request.method} {request.url.path} - "
#             f"{response.status_code} - {duration:.2f}ms"
#         )
#         return response
#
# app.add_middleware(LoggingMiddleware)


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with service information.
    """
    return {
        "service": settings.SERVICE_NAME,
        "version": app.version,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for service monitoring.

    Returns service status, version, and uptime information.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": app.version,
        "redis_enabled": settings.REDIS_ENABLED,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe for Kubernetes.

    Checks if the service is ready to accept traffic.
    Currently simple - will be expanded with dependency checks.
    """
    # TODO: Check database connectivity
    # TODO: Check Redis connectivity
    # TODO: Check RabbitMQ connectivity

    return {
        "status": "ready",
        "service": settings.SERVICE_NAME,
        "version": app.version,
    }


@app.get("/version", tags=["Root"])
async def get_version() -> Dict[str, str]:
    """
    Get the service version.
    """
    return {
        "service": settings.SERVICE_NAME,
        "version": app.version,
    }


# ============================================
# OPTIONAL: METRICS ENDPOINT (Prometheus)
# ============================================

# @app.get("/metrics", tags=["Monitoring"])
# async def get_metrics():
#     """
#     Prometheus metrics endpoint.
#     """
#     from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
#     return Response(
#         generate_latest(),
#         media_type=CONTENT_TYPE_LATEST,
#     )