"""API v1 router for the API Gateway service.

This module aggregates all v1 API routes and provides the main router
for the API Gateway. It includes:
- Authentication endpoints (auth)
- Prediction endpoints (predictions)
- Market data endpoints (market)
- Alert endpoints (alerts)
- Export endpoints (exports)
"""

from fastapi import APIRouter

# Import all route modules
from app.api.v1 import auth
from app.api.v1 import predictions
from app.api.v1 import market  # Added: Market data endpoints
# from app.api.v1 import alerts       # Will be added later
# from app.api.v1 import exports      # Will be added later

# ============================================
# MAIN ROUTER
# ============================================

router = APIRouter(prefix="/api/v1", tags=["API v1"])

# ============================================
# INCLUDE ROUTES
# ============================================

# Authentication routes (auth.router already has prefix="/auth")
router.include_router(auth.router)

# Prediction routes
router.include_router(
    predictions.router,
    prefix="/predict",
    tags=["Predictions"],
)

# Market data routes
router.include_router(
    market.router,
    tags=["Market Data"],
)

# Alert routes (to be added)
# router.include_router(
#     alerts.router,
#     prefix="/alerts",
#     tags=["Alerts"],
# )

# Export routes (to be added)
# router.include_router(
#     exports.router,
#     prefix="/export",
#     tags=["Exports"],
# )

# ============================================
# HEALTH CHECK ENDPOINTS (via main app)
# ============================================

# Health check endpoints are defined in app/main.py
# No need to duplicate them here


# ============================================
# ROOT ENDPOINT (for v1)
# ============================================

@router.get("", tags=["Root"])
async def api_v1_root():
    """
    API v1 root endpoint with service information.
    """
    return {
        "version": "v1",
        "service": "api-gateway",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": {
                "register": "POST /api/v1/auth/register",
                "login": "POST /api/v1/auth/login",
                "refresh": "POST /api/v1/auth/refresh",
                "me": "GET /api/v1/auth/me",
                "logout": "POST /api/v1/auth/logout",
                "change_password": "POST /api/v1/auth/change-password",
                "verify": "GET /api/v1/auth/verify",
            },
            "predictions": {
                "btc": "GET /api/v1/predict/btc?horizon=24h&model_type=ensemble",
                "accuracy": "GET /api/v1/predict/btc/accuracy?days=30",
            },
            "market_data": {
                "prices": "GET /api/v1/btc/prices?limit=100&offset=0",
                "indicators": "GET /api/v1/indicators",
                "correlation": "GET /api/v1/correlation/btc?window=30d",
                "regimes": "GET /api/v1/regimes/btc?timeframe=1w",
            },
            "alerts": "Coming soon",
            "exports": "Coming soon",
        },
    }