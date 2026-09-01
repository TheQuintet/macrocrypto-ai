# """Predictions API endpoints for BTC price predictions.

# This module provides REST API endpoints for fetching BTC predictions
# with different horizons (24h, 7d) and model types.
# """

# import httpx
# import logging
# import json
# from typing import Optional, List, Dict, Any
# from datetime import datetime, timezone

# from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
# from fastapi.security import HTTPBearer
# from pydantic import BaseModel, Field
# from sqlalchemy.orm import Session

# from app.core.config import settings
# from app.core.security import get_current_active_user
# from app.core.rate_limiter import RateLimiter
# from app.cache.service import cache_service
# from app.services.prediction_service import prediction_service
# from app.models.user import User

# # ============================================
# # LOGGING
# # ============================================

# logger = logging.getLogger(settings.SERVICE_NAME)

# # ============================================
# # ROUTER
# # ============================================

# router = APIRouter(tags=["Predictions"])
# security = HTTPBearer()


# # ============================================
# # PYDANTIC MODELS
# # ============================================

# class PredictionPoint(BaseModel):
#     """Single prediction data point."""

#     timestamp: str = Field(..., description="Timestamp of the prediction")
#     price: float = Field(..., description="Predicted price")
#     lower_bound: Optional[float] = Field(None, description="Lower confidence bound")
#     upper_bound: Optional[float] = Field(None, description="Upper confidence bound")
#     confidence: Optional[float] = Field(None, description="Confidence level (0-1)")


# class PredictionResponse(BaseModel):
#     """Prediction response model."""

#     symbol: str = Field(..., description="Trading symbol")
#     timeframe: str = Field(..., description="Prediction timeframe")
#     model_type: str = Field(..., description="Model type used")
#     current_price: float = Field(..., description="Current BTC price")
#     change_percent: Optional[float] = Field(None, description="Percentage change")
#     trend_direction: str = Field(..., description="Trend direction: up/down/neutral")
#     predictions: List[PredictionPoint] = Field(..., description="List of predictions")
#     timestamp: str = Field(..., description="Response timestamp")
#     cached: bool = Field(False, description="Whether response was cached")


# class ErrorResponse(BaseModel):
#     """Error response model."""

#     detail: str = Field(..., description="Error message")


# # ============================================
# # ENDPOINTS
# # ============================================

# @router.get(
#     "/btc",
#     response_model=PredictionResponse,
#     responses={
#         200: {"description": "Successful response"},
#         401: {"description": "Unauthorized", "model": ErrorResponse},
#         429: {"description": "Rate limit exceeded", "model": ErrorResponse},
#         503: {"description": "Service unavailable", "model": ErrorResponse},
#     },
# )
# async def get_btc_predictions(
#     request: Request,
#     horizon: str = Query(
#         "24h",
#         description="Prediction horizon: '24h' or '7d'",
#         pattern="^(24h|7d)$"
#     ),
#     model_type: str = Query(
#         "ensemble",
#         description="Model type: 'ensemble', 'lstm', 'transformer'",
#         pattern="^(ensemble|lstm|transformer)$"
#     ),
#     current_user: User = Depends(get_current_active_user),
# ):
#     """
#     Get BTC price predictions.

#     Returns BTC predictions for the specified horizon (24h or 7d)
#     using the specified model type.

#     Args:
#         request: The HTTP request object.
#         horizon: Prediction horizon (24h or 7d).
#         model_type: Model type (ensemble, lstm, transformer).
#         current_user: The authenticated user.

#     Returns:
#         PredictionResponse: The prediction data.

#     Raises:
#         HTTPException: If the AI Service is unavailable or returns an error.
#     """
#     # Try to get from cache using cache service
#     cached_data = await cache_service.get_predictions("BTC", horizon, model_type)
#     if cached_data:
#         import json
#         logger.info(f"Cache hit for predictions_btc_{horizon}_{model_type}")
#         if isinstance(cached_data, dict):
#             cached_data["cached"] = True
#         return cached_data

#     try:
#         # Fetch predictions from AI Service
#         predictions = await prediction_service.get_predictions(
#             symbol="BTC",
#             timeframe=horizon,
#             model_type=model_type,
#         )

#         # Cache the response using cache service
#         await cache_service.set_predictions("BTC", horizon, model_type, predictions)
#         logger.info(f"Cached predictions for BTC_{horizon}_{model_type}")

#         return predictions

#     except httpx.HTTPStatusError as e:
#         logger.error(f"AI Service error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=f"AI Service unavailable: {e.response.status_code}"
#         )
#     except httpx.TimeoutException:
#         logger.error("AI Service timeout")
#         raise HTTPException(
#             status_code=status.HTTP_504_GATEWAY_TIMEOUT,
#             detail="AI Service request timed out"
#         )
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to fetch predictions: {str(e)}"
#         )


# @router.get(
#     "/btc/accuracy",
#     responses={
#         200: {"description": "Successful response"},
#         401: {"description": "Unauthorized"},
#         503: {"description": "Service unavailable"},
#     },
# )
# async def get_btc_accuracy(
#     request: Request,
#     days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
#     current_user: User = Depends(get_current_active_user),
# ):
#     """
#     Get BTC prediction accuracy metrics.

#     Returns accuracy metrics for BTC predictions over the specified number of days.

#     Args:
#         request: The HTTP request object.
#         days: Number of days to analyze.
#         current_user: The authenticated user.

#     Returns:
#         Dict: Accuracy metrics.
#     """
#     # Try to get from cache using cache service
#     cached_data = await cache_service.get_accuracy("BTC", days)
#     if cached_data:
#         import json
#         logger.info(f"Cache hit for accuracy_btc_{days}")
#         if isinstance(cached_data, dict):
#             cached_data["cached"] = True
#         return cached_data

#     try:
#         accuracy_data = await prediction_service.get_accuracy_metrics(
#             symbol="BTC",
#             days=days,
#         )

#         # Cache the response using cache service
#         await cache_service.set_accuracy("BTC", days, accuracy_data)
#         logger.info(f"Cached accuracy for BTC_{days}")

#         return accuracy_data

#     except httpx.HTTPStatusError as e:
#         logger.error(f"AI Service error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail=f"AI Service unavailable: {e.response.status_code}"
#         )
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to fetch accuracy: {str(e)}"
#         )