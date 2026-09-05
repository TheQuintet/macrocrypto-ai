# """Integration tests for recommendations endpoints."""

# import pytest
# import time
# from fastapi.testclient import TestClient
# from unittest.mock import patch

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
#     username = f"recuser{unique}"
#     email = f"rec{unique}@example.com"

#     register_response = client.post(
#         "/api/v1/auth/register",
#         json={
#             "email": email,
#             "username": username,
#             "password": "TestPass123",
#             "full_name": "Rec User"
#         }
#     )
#     user_id = register_response.json()["id"]

#     user = db_session.query(User).filter(User.id == user_id).first()
#     user.status = UserStatus.ACTIVE
#     user.is_email_verified = True
#     db_session.commit()

#     login_response = client.post(
#         "/api/v1/auth/login",
#         json={
#             "username": username,
#             "password": "TestPass123"
#         }
#     )
#     return login_response.json()["access_token"]


# class TestRecommendationsIntegration:
#     """Integration tests for recommendations endpoints."""

#     @patch("app.api.v1.recommendations.prediction_service.get_predictions")
#     def test_get_recommendations(self, mock_get_predictions, client, auth_token):
#         """Test getting trade recommendations."""
#         mock_get_predictions.return_value = {
#             "symbol": "BTC",
#             "timeframe": "24h",
#             "model_type": "ensemble",
#             "current_price": 45000.00,
#             "change_percent": 2.5,
#             "trend_direction": "up",
#             "predictions": [
#                 {"timestamp": "2026-08-28T...", "price": 45500.00, "confidence": 0.85}
#             ],
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/recommendations/btc?timeframe=24h&risk_level=moderate",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["symbol"] == "BTC"
#         assert data["timeframe"] == "24h"
#         assert data["risk_level"] == "moderate"
#         assert "recommendation" in data
#         assert data["recommendation"]["recommendation"] in ["BUY", "SELL", "HOLD"]
#         assert "entry_price" in data["recommendation"]
#         assert "stop_loss" in data["recommendation"]
#         assert "take_profit" in data["recommendation"]
#         assert "confidence" in data["recommendation"]
#         assert "explanation" in data["recommendation"]

#     @patch("app.api.v1.recommendations.prediction_service.get_predictions")
#     def test_get_recommendations_7d(self, mock_get_predictions, client, auth_token):
#         """Test getting 7d trade recommendations."""
#         mock_get_predictions.return_value = {
#             "symbol": "BTC",
#             "timeframe": "7d",
#             "model_type": "ensemble",
#             "current_price": 45000.00,
#             "change_percent": 5.0,
#             "trend_direction": "up",
#             "predictions": [
#                 {"timestamp": "2026-08-28T...", "price": 47000.00, "confidence": 0.80}
#             ],
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/recommendations/btc?timeframe=7d&risk_level=high",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["timeframe"] == "7d"
#         assert data["risk_level"] == "high"
#         assert data["recommendation"]["time_horizon"] == "7d"

#     @patch("app.api.v1.recommendations.prediction_service.get_predictions")
#     def test_get_recommendations_low_risk(self, mock_get_predictions, client, auth_token):
#         """Test getting low risk trade recommendations."""
#         mock_get_predictions.return_value = {
#             "symbol": "BTC",
#             "timeframe": "24h",
#             "model_type": "ensemble",
#             "current_price": 45000.00,
#             "change_percent": 2.5,
#             "trend_direction": "up",
#             "predictions": [
#                 {"timestamp": "2026-08-28T...", "price": 45500.00, "confidence": 0.85}
#             ],
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/recommendations/btc?timeframe=24h&risk_level=low",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["risk_level"] == "low"
#         assert data["recommendation"]["risk_level"] == "low"

#     @patch("app.api.v1.recommendations.prediction_service.get_predictions")
#     def test_get_recommendations_hold(self, mock_get_predictions, client, auth_token):
#         """Test getting HOLD recommendation."""
#         mock_get_predictions.return_value = {
#             "symbol": "BTC",
#             "timeframe": "24h",
#             "model_type": "ensemble",
#             "current_price": 45000.00,
#             "change_percent": 0.5,
#             "trend_direction": "neutral",
#             "predictions": [
#                 {"timestamp": "2026-08-28T...", "price": 45100.00, "confidence": 0.70}
#             ],
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/recommendations/btc?timeframe=24h&risk_level=moderate",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["recommendation"]["recommendation"] == "HOLD"

#     def test_recommendations_unauthenticated(self, client):
#         """Test recommendations endpoint without authentication."""
#         response = client.get("/api/v1/recommendations/btc")
#         assert response.status_code == 401

#     def test_recommendations_invalid_timeframe(self, client, auth_token):
#         """Test recommendations with invalid timeframe."""
#         response = client.get(
#             "/api/v1/recommendations/btc?timeframe=invalid",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )
#         assert response.status_code == 422

#     def test_recommendations_invalid_risk(self, client, auth_token):
#         """Test recommendations with invalid risk level."""
#         response = client.get(
#             "/api/v1/recommendations/btc?risk_level=invalid",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )
#         assert response.status_code == 422