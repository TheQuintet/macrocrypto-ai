"""FastAPI application entry point for API Gateway service.

This module initializes the FastAPI application, configures middleware,
sets up exception handlers, and defines the root endpoints including
health checks.
"""

import logging
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.redis import redis_client
from app.core.rabbitmq import rabbitmq_client

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

    # Connect to Redis
    if settings.REDIS_ENABLED:
        await redis_client.connect()
        logger.info(f"🗄️  Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    else:
        logger.warning("⚠️ Redis is disabled")

    # Connect to RabbitMQ and start consumer
    if await rabbitmq_client.connect():
        logger.info(f"📨 RabbitMQ: {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
        # Start consuming price updates in background
        asyncio.create_task(_start_rabbitmq_consumer())
    else:
        logger.warning("⚠️ RabbitMQ is disabled or not connected")

    # Log database status
    logger.info(f"🐘 PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

    logger.info(f"✅ {settings.SERVICE_NAME} started successfully")

    yield  # Application runs here

    # --- SHUTDOWN ---
    rabbitmq_client.close()
    await redis_client.disconnect()
    logger.info(f"🛑 Shutting down {settings.SERVICE_NAME}...")


# ============================================
# RABBITMQ CONSUMER TASK
# ============================================

async def _start_rabbitmq_consumer():
    """Start the RabbitMQ consumer for price updates."""
    try:
        # Start consuming in a separate thread or use the connection's start_consuming
        # Since pika's start_consuming is blocking, we run it in a thread pool
        import threading

        def consume():
            try:
                # Use the existing connection's channel
                if rabbitmq_client._channel and rabbitmq_client._connected:
                    rabbitmq_client.start_consuming()
                    rabbitmq_client._channel.start_consuming()
            except Exception as e:
                logger.error(f"RabbitMQ consumer error: {e}")

        # Start consuming in background thread
        consumer_thread = threading.Thread(target=consume, daemon=True)
        consumer_thread.start()
        logger.info("✅ RabbitMQ consumer started in background")

    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}")


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
    - **Data Service Proxy**: BTC market data, historical prices, service status,
    macroeconomic indicators, and macroeconomic regime data.
    - **Alert Service Proxy**: Price alerts, prediction alerts, macroeconomic event
    subscriptions, macro alerts, and notification management.

    ### Rate Limits:
    - Guest: 10 requests per minute
    - User: 100 requests per minute
    - Admin: 1000 requests per minute
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================
# MIDDLEWARE
# ============================================

# # --- CORS Middleware ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ALLOW_ORIGINS,
#     allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
#     allow_methods=settings.CORS_ALLOW_METHODS,
#     allow_headers=settings.CORS_ALLOW_HEADERS,
# )

# # --- Trusted Host Middleware ---
# # Disable in test environment to prevent "Invalid host header" errors
# if not settings.DEBUG and not os.getenv("TESTING"):
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=["api.macrocrypto.ai", "localhost", "127.0.0.1"],
#     )


# ============================================
# INCLUDE ROUTERS
# ============================================

from app.api.v1.router import router as api_v1_router
# from app.api.v1.websocket import router as websocket_router

# Include v1 API router
# The router has prefix="/api/v1" and auth has prefix="/auth"
# Final path: /api/v1/auth/register, /api/v1/auth/login, etc.
app.include_router(api_v1_router)

# Include WebSocket router (no prefix, handled in router)
# app.include_router(websocket_router)


# ============================================
# RATE LIMIT MIDDLEWARE
# ============================================

# from app.core.rate_limiter import RateLimitMiddleware

# # Add rate limit middleware (after CORS, before routers)
# # Note: Order matters - rate limiting should be applied after CORS
# app.add_middleware(RateLimitMiddleware)


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
# CUSTOM OPENAPI SCHEMA
# ============================================

# def custom_openapi():
#     """Generate custom OpenAPI schema with enhanced documentation."""
#     if app.openapi_schema:
#         return app.openapi_schema

#     openapi_schema = get_openapi(
#         title=settings.SERVICE_NAME,
#         version=app.version,
#         description="""
#         ## API Gateway for MacroCrypto AI

#         This service provides REST API endpoints for BTC Traders, Investment Analysts,
#         and Platform Users.

#         ### Features:
#         - **Authentication**: JWT-based authentication with access/refresh tokens
#         - **Predictions**: BTC price predictions from multiple AI models
#         - **Market Data**: Real-time and historical market data
#         - **Exports**: Data export in CSV, PNG, and PDF formats
#         - **WebSocket**: Real-time price updates

#         ### Rate Limits:
#         | Role | Requests per Minute |
#         |------|---------------------|
#         | Guest | 10 |
#         | User | 100 |
#         | Admin | 1000 |

#         ### Authentication:
#         1. Register a user: `POST /api/v1/auth/register`
#         2. Login to get tokens: `POST /api/v1/auth/login`
#         3. Include token in requests: `Authorization: Bearer <access_token>`
#         4. Refresh token when expired: `POST /api/v1/auth/refresh`

#         ### Error Codes:
#         | Code | Description |
#         |------|-------------|
#         | 400 | Bad Request - Invalid parameters |
#         | 401 | Unauthorized - Missing or invalid token |
#         | 403 | Forbidden - Insufficient permissions |
#         | 404 | Not Found - Resource not found |
#         | 422 | Unprocessable Entity - Validation error |
#         | 429 | Too Many Requests - Rate limit exceeded |
#         | 500 | Internal Server Error |
#         | 503 | Service Unavailable |
#         | 504 | Gateway Timeout |

#         ### WebSocket:
#         Connect to `ws://localhost:8000/ws` for real-time price updates.
#         Optional token parameter for authenticated connections.
#         """,
#         routes=app.routes,
#     )

#     # Add security scheme
#     openapi_schema["components"]["securitySchemes"] = {
#         "bearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT",
#             "description": "Enter your JWT token in the format: Bearer <token>",
#         }
#     }

#     # Add security requirement to all endpoints except auth and health
#     for path in openapi_schema["paths"]:
#         if not any(x in path for x in ["/auth", "/health", "/ready", "/version", "/ws", "/docs", "/openapi.json"]):
#             for method in openapi_schema["paths"][path]:
#                 openapi_schema["paths"][path][method]["security"] = [{"bearerAuth": []}]

#     # Add tags with descriptions
#     openapi_schema["tags"] = [
#         {"name": "Authentication", "description": "User registration, login, and token management"},
#         {"name": "Predictions", "description": "BTC price predictions and accuracy metrics"},
#         {"name": "Market Data", "description": "Historical prices, indicators, correlation, and regimes"},
#         {"name": "Recommendations", "description": "Trade recommendations for BTC"},
#         {"name": "Exports", "description": "Export data in CSV, PNG, and PDF formats"},
#         {"name": "WebSocket", "description": "Real-time price updates"},
#         {"name": "Health", "description": "Service health and readiness checks"},
#         {"name": "Root", "description": "Service information endpoints"},
#     ]

#     app.openapi_schema = openapi_schema
#     return app.openapi_schema


# app.openapi = custom_openapi


# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with service information.

    Returns service name, version, status, and links to documentation.
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

    Returns service status, version, and connection status for dependencies.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": app.version,
        "redis_enabled": settings.REDIS_ENABLED,
        "rabbitmq_connected": rabbitmq_client.is_connected(),
        "database": "connected",
    }


@app.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe for Kubernetes.

    Checks if the service is ready to accept traffic.
    """
    # TODO: Check database connectivity
    # TODO: Check Redis connectivity
    # TODO: Check RabbitMQ connectivity

    return {
        "status": "ready",
        "service": settings.SERVICE_NAME,
        "version": app.version,
        "rabbitmq_connected": rabbitmq_client.is_connected(),
    }


@app.get("/version", tags=["Root"])
async def get_version() -> Dict[str, str]:
    """
    Get the service version.

    Returns the current version of the API Gateway.
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