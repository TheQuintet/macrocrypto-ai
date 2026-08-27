"""Unit tests for recommendations API endpoints."""

import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserStatus, UserRole
from app.core.security import get_password_hash


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session for tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def active_user(db_session):
    """Create an active test user with unique email."""
    unique = str(int(time.time() * 1000000))
    user = User(
        email=f"testrec{unique}@example.com",
        username=f"testrec{unique}",
        hashed_password=get_password_hash("TestPass123"),
        full_name="Test Rec User",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    # Cleanup after test
    db_session.delete(user)
    db_session.commit()


@pytest.fixture
def access_token(client, active_user):
    """Get an access token for the active user."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": active_user.username,
            "password": "TestPass123"
        }
    )
    return response.json()["access_token"]


class TestRecommendationsEndpoint:
    """Test recommendations API endpoint."""

    def test_recommendations_endpoint_unauthenticated(self, client):
        """Test recommendations endpoint without authentication."""
        response = client.get("/api/v1/recommendations/btc")
        assert response.status_code == 401
        assert "Not authenticated" in response.text

    @patch("app.api.v1.recommendations.prediction_service.get_predictions")
    def test_recommendations_endpoint_success(self, mock_get_predictions, client, access_token):
        """Test successful recommendations response."""
        # Mock prediction service response
        mock_get_predictions.return_value = {
            "symbol": "BTC",
            "timeframe": "24h",
            "model_type": "ensemble",
            "current_price": 45000.00,
            "change_percent": 2.5,
            "trend_direction": "up",
            "predictions": [
                {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45200.00, "confidence": 0.85},
                {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45500.00, "confidence": 0.82},
                {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45800.00, "confidence": 0.79},
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

        response = client.get(
            "/api/v1/recommendations/btc?timeframe=24h&risk_level=moderate",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC"
        assert data["timeframe"] == "24h"
        assert data["risk_level"] == "moderate"
        assert "recommendation" in data
        assert data["recommendation"]["recommendation"] in ["BUY", "SELL", "HOLD"]
        assert "entry_price" in data["recommendation"]
        assert "stop_loss" in data["recommendation"]
        assert "take_profit" in data["recommendation"]
        assert "confidence" in data["recommendation"]
        assert "explanation" in data["recommendation"]
        assert data["cached"] is False

    @patch("app.api.v1.recommendations.prediction_service.get_predictions")
    def test_recommendations_endpoint_7d(self, mock_get_predictions, client, access_token):
        """Test recommendations with 7d timeframe."""
        mock_get_predictions.return_value = {
            "symbol": "BTC",
            "timeframe": "7d",
            "model_type": "ensemble",
            "current_price": 45000.00,
            "change_percent": 5.0,
            "trend_direction": "up",
            "predictions": [
                {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45500.00, "confidence": 0.80},
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

        response = client.get(
            "/api/v1/recommendations/btc?timeframe=7d&risk_level=high",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["timeframe"] == "7d"
        assert data["risk_level"] == "high"
        assert data["recommendation"]["time_horizon"] == "7d"

    @patch("app.api.v1.recommendations.prediction_service.get_predictions")
    def test_recommendations_endpoint_low_risk(self, mock_get_predictions, client, access_token):
        """Test recommendations with low risk level."""
        mock_get_predictions.return_value = {
            "symbol": "BTC",
            "timeframe": "24h",
            "model_type": "ensemble",
            "current_price": 45000.00,
            "change_percent": 2.5,
            "trend_direction": "up",
            "predictions": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

        response = client.get(
            "/api/v1/recommendations/btc?timeframe=24h&risk_level=low",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "low"
        # Low risk should have tighter stop-loss/take-profit
        stop_loss = data["recommendation"]["stop_loss"]
        take_profit = data["recommendation"]["take_profit"]
        # Stop loss should be closer to entry price for low risk
        assert stop_loss > 0
        assert take_profit > 0

    @patch("app.api.v1.recommendations.prediction_service.get_predictions")
    def test_recommendations_endpoint_hold(self, mock_get_predictions, client, access_token):
        """Test recommendations when trend is neutral (HOLD)."""
        mock_get_predictions.return_value = {
            "symbol": "BTC",
            "timeframe": "24h",
            "model_type": "ensemble",
            "current_price": 45000.00,
            "change_percent": 0.5,
            "trend_direction": "neutral",
            "predictions": [
                {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45050.00, "confidence": 0.70},
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

        response = client.get(
            "/api/v1/recommendations/btc?timeframe=24h&risk_level=moderate",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"]["recommendation"] == "HOLD"

    @patch("app.api.v1.recommendations.prediction_service.get_predictions")
    def test_recommendations_endpoint_invalid_timeframe(self, mock_get_predictions, client, access_token):
        """Test recommendations with invalid timeframe parameter."""
        response = client.get(
            "/api/v1/recommendations/btc?timeframe=invalid",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 422

    @patch("app.api.v1.recommendations.prediction_service.get_predictions")
    def test_recommendations_endpoint_invalid_risk(self, mock_get_predictions, client, access_token):
        """Test recommendations with invalid risk level."""
        response = client.get(
            "/api/v1/recommendations/btc?risk_level=invalid",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 422

    @patch("app.api.v1.recommendations.prediction_service.get_predictions")
    def test_recommendations_endpoint_service_unavailable(self, mock_get_predictions, client, access_token):
        """Test recommendations when AI Service is unavailable."""
        import httpx
        mock_get_predictions.side_effect = httpx.HTTPStatusError(
            "Service unavailable",
            request=MagicMock(),
            response=MagicMock(status_code=503)
        )

        response = client.get(
            "/api/v1/recommendations/btc?timeframe=24h",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 503
        assert "AI Service unavailable" in response.text

    @patch("app.api.v1.recommendations.prediction_service.get_predictions")
    def test_recommendations_endpoint_timeout(self, mock_get_predictions, client, access_token):
        """Test recommendations when AI Service times out."""
        import httpx
        mock_get_predictions.side_effect = httpx.TimeoutException("Request timed out")

        response = client.get(
            "/api/v1/recommendations/btc?timeframe=24h",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 504
        assert "request timed out" in response.text.lower()