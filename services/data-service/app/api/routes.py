"""API routes for data-service"""

from fastapi import APIRouter

from app.api.btc import router as btc_router
from app.api.indicators import router as indicators_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(btc_router)
router.include_router(indicators_router)

# You can add other routers here later
# from app.api.routes.economic import router as economic_router
# router.include_router(economic_router)