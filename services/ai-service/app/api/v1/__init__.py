"""AI Service — v1 API routers.

Each module in this package exposes a FastAPI APIRouter. Routers
are registered in app/main.py.

Available routers:
    - predict: /api/v1/predict/btc
"""

from app.api.v1.predict import router as predict_router

__all__ = [
    "predict_router",
]