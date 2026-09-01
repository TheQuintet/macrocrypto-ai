# """Unit tests for predictions API endpoints."""

# import pytest
# import json
# import time
# from unittest.mock import AsyncMock, patch, MagicMock
# from fastapi.testclient import TestClient
# from datetime import datetime, timezone

# from app.main import app
# from app.core.database import SessionLocal
# from app.models.user import User, UserStatus, UserRole
# from app.core.security import get_password_hash


# @pytest.fixture
# def client():
#     """Create test client."""
#     return TestClient(app)


# @pytest.fixture
# def db_session():
#     """Create database session for tests."""
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.rollback()
#         db.close()


# @pytest.fixture
# def active_user(db_session):
#     """Create an active test user with unique email."""
#     unique = str(int(time.time()))
#     user = User(
#         email=f"testpredict{unique}@example.com",
#         username=f"testpredict{unique}",
#         hashed_password=get_password_hash("TestPass123"),
#         full_name="Test Predict User",
#         role=UserRole.USER,
#         status=UserStatus.ACTIVE,
#         is_email_verified=True,
#     )
#     db_session.add(user)
#     db_session.commit()
#     db_session.refresh(user)
#     return user


# @pytest.fixture
# def access_token(client, active_user):
#     """Get an access token for the active user."""
#     response = client.post(
#         "/api/v1/auth/login",
#         json={
#             "username": active_user.username,
#             "password": "TestPass123"
#         }
#     )
#     return response.json()["access_token"]


# class TestPredictionsEndpoint:
#     """Test predictions API endpoint."""

#     def test_predictions_endpoint_unauthenticated(self, client):
#         """Test predictions endpoint without authentication."""
#         response = client.get("/api/v1/predict/btc")
#         assert response.status_code == 401
#         assert "Not authenticated" in response.text

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_predictions_endpoint_success(self, mock_get_predictions, client, access_token):
#         """Test successful predictions response."""
#         # Mock the prediction service response
#         mock_response = {
#             "symbol": "BTC",
#             "timeframe": "24h",
#             "model_type": "ensemble",
#             "current_price": 45000.00,
#             "change_percent": 2.5,
#             "trend_direction": "up",
#             "predictions": [
#                 {
#                     "timestamp": datetime.now(timezone.utc).isoformat(),
#                     "price": 45100.00,
#                     "lower_bound": 44800.00,
#                     "upper_bound": 45400.00,
#                     "confidence": 0.85,
#                 },
#                 {
#                     "timestamp": datetime.now(timezone.utc).isoformat(),
#                     "price": 45200.00,
#                     "lower_bound": 44900.00,
#                     "upper_bound": 45500.00,
#                     "confidence": 0.82,
#                 },
#             ],
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "cached": False,
#         }
#         mock_get_predictions.return_value = mock_response

#         response = client.get(
#             "/api/v1/predict/btc?horizon=24h&model_type=ensemble",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["symbol"] == "BTC"
#         assert data["timeframe"] == "24h"
#         assert data["model_type"] == "ensemble"
#         assert data["current_price"] == 45000.00
#         assert data["trend_direction"] == "up"
#         assert len(data["predictions"]) == 2
#         assert data["cached"] is False

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_predictions_endpoint_7d(self, mock_get_predictions, client, access_token):
#         """Test 7-day predictions."""
#         mock_response = {
#             "symbol": "BTC",
#             "timeframe": "7d",
#             "model_type": "ensemble",
#             "current_price": 45000.00,
#             "change_percent": 5.0,
#             "trend_direction": "up",
#             "predictions": [
#                 {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45100.00},
#                 {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45200.00},
#                 {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45300.00},
#                 {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45400.00},
#                 {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45500.00},
#                 {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45600.00},
#                 {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45700.00},
#             ],
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "cached": False,
#         }
#         mock_get_predictions.return_value = mock_response

#         response = client.get(
#             "/api/v1/predict/btc?horizon=7d&model_type=ensemble",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["timeframe"] == "7d"
#         assert len(data["predictions"]) == 7

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_predictions_endpoint_lstm_model(self, mock_get_predictions, client, access_token):
#         """Test predictions with LSTM model."""
#         mock_get_predictions.return_value = {
#             "symbol": "BTC",
#             "timeframe": "24h",
#             "model_type": "lstm",
#             "current_price": 45000.00,
#             "change_percent": 2.5,
#             "trend_direction": "up",
#             "predictions": [],
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "cached": False,
#         }

#         response = client.get(
#             "/api/v1/predict/btc?horizon=24h&model_type=lstm",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["model_type"] == "lstm"

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_predictions_endpoint_invalid_horizon(self, mock_get_predictions, client, access_token):
#         """Test predictions with invalid horizon parameter."""
#         response = client.get(
#             "/api/v1/predict/btc?horizon=invalid",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 422  # Validation error

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_predictions_endpoint_invalid_model(self, mock_get_predictions, client, access_token):
#         """Test predictions with invalid model type."""
#         response = client.get(
#             "/api/v1/predict/btc?model_type=invalid",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 422  # Validation error

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_predictions_endpoint_service_unavailable(self, mock_get_predictions, client, access_token):
#         """Test predictions when AI Service is unavailable."""
#         import httpx
#         mock_get_predictions.side_effect = httpx.HTTPStatusError(
#             "Service unavailable",
#             request=MagicMock(),
#             response=MagicMock(status_code=503)
#         )

#         response = client.get(
#             "/api/v1/predict/btc?horizon=24h",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 503
#         assert "AI Service unavailable" in response.text

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_predictions_endpoint_timeout(self, mock_get_predictions, client, access_token):
#         """Test predictions when AI Service times out."""
#         import httpx
#         mock_get_predictions.side_effect = httpx.TimeoutException("Request timed out")

#         response = client.get(
#             "/api/v1/predict/btc?horizon=24h",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 504
#         assert "request timed out" in response.text.lower()


# class TestAccuracyEndpoint:
#     """Test predictions accuracy endpoint."""

#     def test_accuracy_endpoint_unauthenticated(self, client):
#         """Test accuracy endpoint without authentication."""
#         response = client.get("/api/v1/predict/btc/accuracy")
#         assert response.status_code == 401
#         assert "Not authenticated" in response.text

#     @patch("app.api.v1.predictions.prediction_service.get_accuracy_metrics")
#     def test_accuracy_endpoint_success(self, mock_get_accuracy, client, access_token):
#         """Test successful accuracy response."""
#         mock_response = {
#             "symbol": "BTC",
#             "days": 30,
#             "overall_accuracy": 85.5,
#             "rmse": 125.30,
#             "mae": 98.75,
#             "mape": 2.1,
#             "predictions_count": 720,
#             "market_condition_breakdown": {
#                 "bull": {"accuracy": 88.0, "count": 240},
#                 "bear": {"accuracy": 82.0, "count": 240},
#                 "sideways": {"accuracy": 86.5, "count": 240},
#             },
#             "threshold_warning": False,
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "cached": False,
#         }
#         mock_get_accuracy.return_value = mock_response

#         response = client.get(
#             "/api/v1/predict/btc/accuracy?days=30",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["symbol"] == "BTC"
#         assert data["days"] == 30
#         assert data["overall_accuracy"] == 85.5
#         assert data["predictions_count"] == 720
#         assert "market_condition_breakdown" in data
#         assert data["threshold_warning"] is False

#     @patch("app.api.v1.predictions.prediction_service.get_accuracy_metrics")
#     def test_accuracy_endpoint_days_range(self, mock_get_accuracy, client, access_token):
#         """Test accuracy with different days parameter."""
#         mock_get_accuracy.return_value = {
#             "symbol": "BTC",
#             "days": 90,
#             "overall_accuracy": 82.0,
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "cached": False,
#         }

#         response = client.get(
#             "/api/v1/predict/btc/accuracy?days=90",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["days"] == 90

#     @patch("app.api.v1.predictions.prediction_service.get_accuracy_metrics")
#     def test_accuracy_endpoint_invalid_days(self, mock_get_accuracy, client, access_token):
#         """Test accuracy with invalid days parameter."""
#         response = client.get(
#             "/api/v1/predict/btc/accuracy?days=400",
#             headers={"Authorization": f"Bearer {access_token}"}
#         )

#         assert response.status_code == 422  # Validation error