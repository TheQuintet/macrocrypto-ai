"""Health check endpoints for AI Service."""

import logging
from datetime import datetime

from fastapi import APIRouter

from app import __version__, __service_name__
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# HEALTH CHECK
# ============================================================
@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns overall service health and component statuses.
    Components will be checked in subsequent branches as
    connections are implemented.
    """
    status = {
        "service": __service_name__,
        "version": __version__,
        "environment": settings.environment.value,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "components": {
            "database": "not_checked",
            "rabbitmq": "not_checked",
            "redis": "not_checked",
            "mlflow": "not_checked",
        },
    }

    return status


# ============================================================
# KUBERNETES PROBES
# ============================================================
@router.get("/health/live")
async def liveness_check():
    """Liveness probe — is the service running?"""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe — is the service ready to serve traffic?"""
    return {"status": "ready"}


# ============================================================
# ROOT HEALTH (for backward compatibility with existing pattern)
# ============================================================
@router.get("/ready")
async def ready_check():
    """Readiness check (matches existing Makefile pattern)."""
    return {"status": "ready"}