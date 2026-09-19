"""AI Service — v1 API routers.

Each module in this package exposes a FastAPI APIRouter. Routers
are registered in app/main.py.

Available routers:
    - predict: /api/v1/predict/btc
    - performance: /api/v1/performance/btc
    - correlation: /api/v1/correlation/btc
"""

from app.api.v1.predict import router as predict_router
from app.api.v1.performance import router as performance_router
from app.api.v1.correlation import router as correlation_router

__all__ = [
    "predict_router",
    "performance_router",
    "correlation_router",
]