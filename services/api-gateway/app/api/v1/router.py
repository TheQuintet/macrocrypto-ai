"""API v1 router for the API Gateway service.

This module aggregates the API Gateway v1 routes.

The API Gateway exposes the existing downstream services through thin
proxy routes. Business logic remains inside the respective services.
"""

from fastapi import APIRouter

from app.api.v1 import auth
from app.api.v1 import service_proxy


# ============================================================================
# MAIN V1 ROUTER
# ============================================================================

router = APIRouter(
    prefix="/api/v1",
)


# ============================================================================
# AUTHENTICATION
# ============================================================================

# auth.router already defines its own /auth prefix.
router.include_router(auth.router)


# ============================================================================
# DATA SERVICE + ALERT SERVICE PROXY
# ============================================================================

router.include_router(service_proxy.router)