"""Unit tests for market data API endpoints."""

import pytest
import time
import json
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
        email=f"testmarket{unique}@example.com",
        username=f"testmarket{unique}",
        hashed_password=get_password_hash("TestPass123"),
        full_name="Test Market User",
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


class TestPricesEndpoint:
    """Test prices API endpoint."""

    def test_prices_endpoint_unauthenticated(self, client):
        """Test prices endpoint without authentication."""
        response = client.get("/api/v1/btc/prices")
        assert response.status_code in [401, 200]

    @patch("app.api.v1.market.market_service.get_prices")
    def test_prices_endpoint_success(self, mock_get_prices, client, access_token):
        """Test successful prices response."""
        mock_response = {
            "symbol": "BTC",
            "prices": [
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "price": 45000.00,
                    "volume": 1500000.00,
                    "market_cap": 855000000000.00,
                },
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "price": 45100.00,
                    "volume": 1200000.00,
                    "market_cap": 856900000000.00,
                },
            ],
            "total": 2,
            "limit": 100,
            "offset": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }
        mock_get_prices.return_value = mock_response

        response = client.get(
            "/api/v1/btc/prices?limit=2&offset=0",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC"
        assert len(data["prices"]) == 2
        assert data["total"] == 2
        assert data["limit"] == 100
        assert data["offset"] == 0
        assert data["cached"] is False

    @patch("app.api.v1.market.market_service.get_prices")
    def test_prices_endpoint_with_date_range(self, mock_get_prices, client, access_token):
        """Test prices with date range filtering."""
        mock_get_prices.return_value = {
            "symbol": "BTC",
            "prices": [],
            "total": 0,
            "limit": 100,
            "offset": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

        response = client.get(
            "/api/v1/btc/prices?start_date=2024-01-01&end_date=2024-01-31",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        mock_get_prices.assert_called_once_with(
            symbol="BTC",
            start_date="2024-01-01",
            end_date="2024-01-31",
            limit=100,
            offset=0,
        )


class TestIndicatorsEndpoint:
    """Test indicators API endpoint."""

    def test_indicators_endpoint_unauthenticated(self, client):
        """Test indicators endpoint without authentication."""
        response = client.get("/api/v1/indicators")
        assert response.status_code in [401, 200]

    @patch("app.api.v1.market.market_service.get_indicators")
    def test_indicators_endpoint_success(self, mock_get_indicators, client, access_token):
        """Test successful indicators response."""
        mock_response = {
            "indicators": {
                "GDP": {"value": 28.78, "previous": 28.52, "change_percent": 0.91, "source": "BEA", "unit": "trillion USD"},
                "Inflation": {"value": 3.2, "previous": 3.5, "change_percent": -8.57, "source": "BLS", "unit": "percent"},
                "Interest Rates": {"value": 5.50, "previous": 5.50, "change_percent": 0.0, "source": "Federal Reserve", "unit": "percent"},
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }
        mock_get_indicators.return_value = mock_response

        response = client.get(
            "/api/v1/indicators",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "indicators" in data
        assert "GDP" in data["indicators"]
        assert data["cached"] is False

    @patch("app.api.v1.market.market_service.get_indicators")
    def test_indicators_endpoint_filtered(self, mock_get_indicators, client, access_token):
        """Test indicators with filtering."""
        mock_get_indicators.return_value = {
            "indicators": {
                "GDP": {"value": 28.78, "previous": 28.52, "change_percent": 0.91, "source": "BEA", "unit": "trillion USD"},
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }

        response = client.get(
            "/api/v1/indicators?indicators=GDP",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        mock_get_indicators.assert_called_once_with(indicators=["GDP"])


class TestCorrelationEndpoint:
    """Test correlation API endpoint."""

    def test_correlation_endpoint_unauthenticated(self, client):
        """Test correlation endpoint without authentication."""
        response = client.get("/api/v1/correlation/btc")
        assert response.status_code in [401, 200]

    @patch("app.api.v1.market.market_service.get_correlation")
    def test_correlation_endpoint_success(self, mock_get_correlation, client, access_token):
        """Test successful correlation response."""
        mock_response = {
            "symbol": "BTC",
            "window": "30d",
            "days": 30,
            "correlations": {
                "S&P 500": {"value": 0.65, "strength": "moderate"},
                "DXY": {"value": -0.45, "strength": "moderate"},
                "Gold": {"value": 0.35, "strength": "weak"},
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }
        mock_get_correlation.return_value = mock_response

        response = client.get(
            "/api/v1/correlation/btc?window=30d",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC"
        assert data["window"] == "30d"
        assert "correlations" in data
        assert data["cached"] is False

    @patch("app.api.v1.market.market_service.get_correlation")
    def test_correlation_endpoint_invalid_window(self, mock_get_correlation, client, access_token):
        """Test correlation with invalid window parameter."""
        response = client.get(
            "/api/v1/correlation/btc?window=invalid",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 422


class TestRegimesEndpoint:
    """Test regimes API endpoint."""

    def test_regimes_endpoint_unauthenticated(self, client):
        """Test regimes endpoint without authentication."""
        response = client.get("/api/v1/regimes/btc")
        assert response.status_code in [401, 200]

    @patch("app.api.v1.market.market_service.get_regimes")
    def test_regimes_endpoint_success(self, mock_get_regimes, client, access_token):
        """Test successful regimes response."""
        mock_response = {
            "symbol": "BTC",
            "timeframe": "1w",
            "regimes": [
                {
                    "regime_type": "bull",
                    "start_date": datetime.now(timezone.utc).isoformat(),
                    "end_date": datetime.now(timezone.utc).isoformat(),
                    "duration_days": 30,
                    "avg_return": 12.5,
                    "max_drawdown": -3.2,
                    "volatility": 18.5,
                    "sharpe_ratio": 2.1,
                }
            ],
            "current_regime": {
                "regime_type": "bull",
                "start_date": datetime.now(timezone.utc).isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat(),
                "duration_days": 30,
                "avg_return": 12.5,
                "max_drawdown": -3.2,
                "volatility": 18.5,
                "sharpe_ratio": 2.1,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cached": False,
        }
        mock_get_regimes.return_value = mock_response

        response = client.get(
            "/api/v1/regimes/btc?timeframe=1w",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "BTC"
        assert data["timeframe"] == "1w"
        assert "regimes" in data
        assert "current_regime" in data
        assert data["cached"] is False

    @patch("app.api.v1.market.market_service.get_regimes")
    def test_regimes_endpoint_invalid_timeframe(self, mock_get_regimes, client, access_token):
        """Test regimes with invalid timeframe parameter."""
        response = client.get(
            "/api/v1/regimes/btc?timeframe=invalid",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 422