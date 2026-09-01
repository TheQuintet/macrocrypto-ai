# """Integration tests for market data endpoints."""

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
#     username = f"marketuser{unique}"
#     email = f"market{unique}@example.com"

#     register_response = client.post(
#         "/api/v1/auth/register",
#         json={
#             "email": email,
#             "username": username,
#             "password": "TestPass123",
#             "full_name": "Market User"
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


# class TestMarketIntegration:
#     """Integration tests for market data endpoints."""

#     @patch("app.api.v1.market.market_service.get_prices")
#     def test_get_prices(self, mock_get_prices, client, auth_token):
#         """Test getting BTC prices."""
#         mock_get_prices.return_value = {
#             "symbol": "BTC",
#             "prices": [
#                 {"timestamp": "2026-08-28T...", "price": 45000.00, "volume": 1500000.00, "market_cap": 855000000000.00}
#             ],
#             "total": 1,
#             "limit": 100,
#             "offset": 0,
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/btc/prices?limit=10&offset=0",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["symbol"] == "BTC"
#         assert "prices" in data
#         assert "total" in data
#         assert "limit" in data

#     @patch("app.api.v1.market.market_service.get_prices")
#     def test_get_prices_with_date_range(self, mock_get_prices, client, auth_token):
#         """Test getting prices with date range."""
#         mock_get_prices.return_value = {
#             "symbol": "BTC",
#             "prices": [],
#             "total": 0,
#             "limit": 100,
#             "offset": 0,
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/btc/prices?start_date=2026-08-01&end_date=2026-08-28",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200

#     @patch("app.api.v1.market.market_service.get_indicators")
#     def test_get_indicators(self, mock_get_indicators, client, auth_token):
#         """Test getting macroeconomic indicators."""
#         mock_get_indicators.return_value = {
#             "indicators": {
#                 "GDP": {"value": 28.78, "previous": 28.52, "change_percent": 0.91, "source": "BEA", "unit": "trillion USD"},
#                 "Inflation": {"value": 3.2, "previous": 3.5, "change_percent": -8.57, "source": "BLS", "unit": "percent"}
#             },
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/indicators",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert "indicators" in data
#         assert "GDP" in data["indicators"]

#     @patch("app.api.v1.market.market_service.get_correlation")
#     def test_get_correlation(self, mock_get_correlation, client, auth_token):
#         """Test getting correlation analysis."""
#         mock_get_correlation.return_value = {
#             "symbol": "BTC",
#             "window": "30d",
#             "days": 30,
#             "correlations": {
#                 "S&P 500": {"value": 0.65, "strength": "moderate"},
#                 "DXY": {"value": -0.45, "strength": "moderate"}
#             },
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/correlation/btc?window=30d",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["symbol"] == "BTC"
#         assert data["window"] == "30d"
#         assert "correlations" in data

#     @patch("app.api.v1.market.market_service.get_regimes")
#     def test_get_regimes(self, mock_get_regimes, client, auth_token):
#         """Test getting regime data."""
#         mock_get_regimes.return_value = {
#             "symbol": "BTC",
#             "timeframe": "1w",
#             "regimes": [
#                 {
#                     "regime_type": "bull",
#                     "start_date": "2026-08-28T00:00:00Z",
#                     "duration_days": 30,
#                     "avg_return": 12.5,
#                     "max_drawdown": -3.2
#                 }
#             ],
#             "current_regime": {
#                 "regime_type": "bull",
#                 "start_date": "2026-08-28T00:00:00Z",
#                 "duration_days": 30,
#                 "avg_return": 12.5
#             },
#             "timestamp": "2026-08-28T...",
#             "cached": False
#         }

#         response = client.get(
#             "/api/v1/regimes/btc?timeframe=1w",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 200
#         data = response.json()
#         assert data["symbol"] == "BTC"
#         assert data["timeframe"] == "1w"
#         assert "regimes" in data
#         assert "current_regime" in data
#         assert "start_date" in data["current_regime"]

#     def test_market_unauthenticated(self, client):
#         """Test market endpoints without authentication."""
#         response = client.get("/api/v1/btc/prices")
#         assert response.status_code == 401