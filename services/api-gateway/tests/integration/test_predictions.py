# """Integration tests for predictions endpoints."""

# import pytest
# import time
# from fastapi.testclient import TestClient
# from unittest.mock import patch, MagicMock

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
# def auth_token(client, db_session):
#     """Create a user and return auth token."""
#     unique = str(int(time.time() * 1000000))
#     username = f"predictuser{unique}"
#     email = f"predict{unique}@example.com"

#     # Register
#     register_response = client.post(
#         "/api/v1/auth/register",
#         json={
#             "email": email,
#             "username": username,
#             "password": "TestPass123",
#             "full_name": "Predict User"
#         }
#     )
#     user_id = register_response.json()["id"]

#     # Verify user
#     user = db_session.query(User).filter(User.id == user_id).first()
#     user.status = UserStatus.ACTIVE
#     user.is_email_verified = True
#     db_session.commit()

#     # Login
#     login_response = client.post(
#         "/api/v1/auth/login",
#         json={
#             "username": username,
#             "password": "TestPass123"
#         }
#     )
#     return login_response.json()["access_token"]


# class TestPredictionsIntegration:
#     """Integration tests for predictions endpoints."""

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_get_predictions_24h(self, mock_get_predictions, client, auth_token):
#         """Test getting 24h predictions."""
#         mock_get_predictions.return_value = {
#             "symbol": "BTC",
#             "timeframe": "24h",
#             "model_type": "ensemble",
#             "current_price": 45000.00,
#             "change_percent": 2.5,
#             "trend_direction": "up",
#             "predictions": [
#                 {"timestamp": "2026-08-28T...", "price": 45100.00, "lower_bound": 44800.00, "upper_bound": 45400.00, "confidence": 0.85}
#             ],
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/predict/btc?horizon=24h&model_type=ensemble",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["symbol"] == "BTC"
#         assert data["timeframe"] == "24h"
#         assert data["model_type"] == "ensemble"
#         assert "current_price" in data
#         assert "predictions" in data
#         assert len(data["predictions"]) > 0

#     @patch("app.api.v1.predictions.prediction_service.get_predictions")
#     def test_get_predictions_7d(self, mock_get_predictions, client, auth_token):
#         """Test getting 7d predictions."""
#         mock_get_predictions.return_value = {
#             "symbol": "BTC",
#             "timeframe": "7d",
#             "model_type": "ensemble",
#             "current_price": 45000.00,
#             "change_percent": 5.0,
#             "trend_direction": "up",
#             "predictions": [
#                 {"timestamp": "2026-08-28T...", "price": 45500.00, "lower_bound": 45000.00, "upper_bound": 46000.00, "confidence": 0.80}
#             ],
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/predict/btc?horizon=7d&model_type=ensemble",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["timeframe"] == "7d"

#     @patch("app.api.v1.predictions.prediction_service.get_accuracy_metrics")
#     def test_get_accuracy(self, mock_get_accuracy, client, auth_token):
#         """Test getting prediction accuracy."""
#         mock_get_accuracy.return_value = {
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
#                 "sideways": {"accuracy": 86.5, "count": 240}
#             },
#             "threshold_warning": False
#         }

#         response = client.get(
#             "/api/v1/predict/btc/accuracy?days=30",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["symbol"] == "BTC"
#         assert data["days"] == 30
#         assert data["overall_accuracy"] == 85.5

#     def test_predictions_unauthenticated(self, client):
#         """Test predictions endpoint without authentication."""
#         response = client.get("/api/v1/predict/btc?horizon=24h")
#         assert response.status_code == 401

#     def test_predictions_invalid_horizon(self, client, auth_token):
#         """Test predictions with invalid horizon."""
#         response = client.get(
#             "/api/v1/predict/btc?horizon=invalid",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )
#         assert response.status_code == 422