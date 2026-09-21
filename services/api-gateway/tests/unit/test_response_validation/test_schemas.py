# """Response format validation tests for all API endpoints."""

# import pytest
# import time
# import json
# from fastapi.testclient import TestClient
# from unittest.mock import patch, MagicMock
# from datetime import datetime, timezone

# from app.main import app
# from app.core.database import SessionLocal
# from app.models.user import User, UserStatus, UserRole
# from app.core.security import get_password_hash
# from app.api.v1.predictions import PredictionResponse, PredictionPoint
# from app.api.v1.market import PricesResponse, IndicatorsResponse, CorrelationResponse, RegimesResponse
# from app.api.v1.recommendations import RecommendationResponse
# from app.api.v1.exports import ExportResponse


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
#     username = f"valuser{unique}"
#     email = f"val{unique}@example.com"

#     register_response = client.post(
#         "/api/v1/auth/register",
#         json={
#             "email": email,
#             "username": username,
#             "password": "TestPass123",
#             "full_name": "Validation User"
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


# class TestResponseSchemas:
#     """Test response schema validation for all endpoints."""

#     def test_predictions_response_schema(self, client, auth_token):
#         """Test predictions response schema validation."""
#         with patch("app.api.v1.predictions.prediction_service.get_predictions") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "timeframe": "24h",
#                 "model_type": "ensemble",
#                 "current_price": 45000.00,
#                 "change_percent": 2.5,
#                 "trend_direction": "up",
#                 "predictions": [
#                     {
#                         "timestamp": datetime.now(timezone.utc).isoformat(),
#                         "price": 45100.00,
#                         "lower_bound": 44800.00,
#                         "upper_bound": 45400.00,
#                         "confidence": 0.85
#                     }
#                 ],
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/predict/btc?horizon=24h",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate required fields
#             assert "symbol" in data
#             assert "timeframe" in data
#             assert "model_type" in data
#             assert "current_price" in data
#             assert "trend_direction" in data
#             assert "predictions" in data
#             assert "timestamp" in data
#             assert "cached" in data

#             # Validate data types
#             assert isinstance(data["symbol"], str)
#             assert isinstance(data["timeframe"], str)
#             assert isinstance(data["current_price"], (int, float))
#             assert isinstance(data["predictions"], list)
#             assert isinstance(data["cached"], bool)

#             # Validate prediction points
#             for pred in data["predictions"]:
#                 assert "timestamp" in pred
#                 assert "price" in pred
#                 assert "lower_bound" in pred
#                 assert "upper_bound" in pred
#                 assert "confidence" in pred
#                 assert isinstance(pred["timestamp"], str)
#                 assert isinstance(pred["price"], (int, float))

#     def test_accuracy_response_schema(self, client, auth_token):
#         """Test accuracy response schema validation."""
#         with patch("app.api.v1.predictions.prediction_service.get_accuracy_metrics") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "days": 30,
#                 "overall_accuracy": 85.5,
#                 "rmse": 125.30,
#                 "mae": 98.75,
#                 "mape": 2.1,
#                 "predictions_count": 720,
#                 "market_condition_breakdown": {
#                     "bull": {"accuracy": 88.0, "count": 240},
#                     "bear": {"accuracy": 82.0, "count": 240},
#                     "sideways": {"accuracy": 86.5, "count": 240}
#                 },
#                 "threshold_warning": False,
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/predict/btc/accuracy?days=30",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate required fields
#             assert "symbol" in data
#             assert "days" in data
#             assert "overall_accuracy" in data
#             assert "rmse" in data
#             assert "mae" in data
#             assert "mape" in data
#             assert "predictions_count" in data
#             assert "market_condition_breakdown" in data
#             assert "threshold_warning" in data

#             # Validate data types
#             assert isinstance(data["symbol"], str)
#             assert isinstance(data["days"], int)
#             assert isinstance(data["overall_accuracy"], (int, float))
#             assert isinstance(data["threshold_warning"], bool)

#     def test_prices_response_schema(self, client, auth_token):
#         """Test prices response schema validation."""
#         with patch("app.api.v1.market.market_service.get_prices") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "prices": [
#                     {
#                         "timestamp": datetime.now(timezone.utc).isoformat(),
#                         "price": 45000.00,
#                         "volume": 1500000.00,
#                         "market_cap": 855000000000.00
#                     }
#                 ],
#                 "total": 1,
#                 "limit": 100,
#                 "offset": 0,
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/btc/prices?limit=1",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate required fields
#             assert "symbol" in data
#             assert "prices" in data
#             assert "total" in data
#             assert "limit" in data
#             assert "offset" in data
#             assert "timestamp" in data

#             # Validate data types
#             assert isinstance(data["symbol"], str)
#             assert isinstance(data["prices"], list)
#             assert isinstance(data["total"], int)
#             assert isinstance(data["limit"], int)
#             assert isinstance(data["offset"], int)

#             # Validate price points
#             for price in data["prices"]:
#                 assert "timestamp" in price
#                 assert "price" in price
#                 assert isinstance(price["timestamp"], str)
#                 assert isinstance(price["price"], (int, float))

#     def test_indicators_response_schema(self, client, auth_token):
#         """Test indicators response schema validation."""
#         with patch("app.api.v1.market.market_service.get_indicators") as mock_get:
#             mock_get.return_value = {
#                 "indicators": {
#                     "GDP": {
#                         "value": 28.78,
#                         "previous": 28.52,
#                         "change_percent": 0.91,
#                         "source": "BEA",
#                         "unit": "trillion USD"
#                     }
#                 },
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/indicators",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate required fields
#             assert "indicators" in data
#             assert "timestamp" in data

#             # Validate indicator data
#             for key, value in data["indicators"].items():
#                 assert "value" in value
#                 assert "source" in value
#                 assert "unit" in value
#                 assert isinstance(key, str)
#                 assert isinstance(value["value"], (int, float))
#                 assert isinstance(value["source"], str)
#                 assert isinstance(value["unit"], str)

#     def test_correlation_response_schema(self, client, auth_token):
#         """Test correlation response schema validation."""
#         with patch("app.api.v1.market.market_service.get_correlation") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "window": "30d",
#                 "days": 30,
#                 "correlations": {
#                     "S&P 500": {"value": 0.65, "strength": "moderate"}
#                 },
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/correlation/btc?window=30d",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate required fields
#             assert "symbol" in data
#             assert "window" in data
#             assert "days" in data
#             assert "correlations" in data
#             assert "timestamp" in data

#             # Validate correlation data
#             for key, value in data["correlations"].items():
#                 assert "value" in value
#                 assert "strength" in value
#                 assert isinstance(key, str)
#                 assert isinstance(value["value"], (int, float))
#                 assert value["strength"] in ["strong", "moderate", "weak"]

#     def test_regimes_response_schema(self, client, auth_token):
#         """Test regimes response schema validation."""
#         with patch("app.api.v1.market.market_service.get_regimes") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "timeframe": "1w",
#                 "regimes": [
#                     {
#                         "regime_type": "bull",
#                         "start_date": datetime.now(timezone.utc).isoformat(),
#                         "duration_days": 30,
#                         "avg_return": 12.5,
#                         "max_drawdown": -3.2
#                     }
#                 ],
#                 "current_regime": {
#                     "regime_type": "bull",
#                     "duration_days": 30,
#                     "avg_return": 12.5
#                 },
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/regimes/btc?timeframe=1w",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate required fields
#             assert "symbol" in data
#             assert "timeframe" in data
#             assert "regimes" in data
#             assert "current_regime" in data
#             assert "timestamp" in data

#             # Validate regime data
#             for regime in data["regimes"]:
#                 assert "regime_type" in regime
#                 assert "start_date" in regime
#                 assert isinstance(regime["regime_type"], str)

#     def test_recommendations_response_schema(self, client, auth_token):
#         """Test recommendations response schema validation."""
#         with patch("app.api.v1.recommendations.prediction_service.get_predictions") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "timeframe": "24h",
#                 "model_type": "ensemble",
#                 "current_price": 45000.00,
#                 "change_percent": 2.5,
#                 "trend_direction": "up",
#                 "predictions": [
#                     {"timestamp": datetime.now(timezone.utc).isoformat(), "price": 45500.00, "confidence": 0.85}
#                 ],
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/recommendations/btc?timeframe=24h&risk_level=moderate",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate required fields
#             assert "symbol" in data
#             assert "timeframe" in data
#             assert "risk_level" in data
#             assert "recommendation" in data
#             assert "timestamp" in data

#             # Validate recommendation fields
#             rec = data["recommendation"]
#             assert "recommendation" in rec
#             assert "confidence" in rec
#             assert "entry_price" in rec
#             assert "stop_loss" in rec
#             assert "take_profit" in rec
#             assert "risk_level" in rec
#             assert "risk_reward_ratio" in rec
#             assert "time_horizon" in rec
#             assert "explanation" in rec
#             assert rec["recommendation"] in ["BUY", "SELL", "HOLD"]

#     def test_error_response_schema(self, client, auth_token):
#         """Test error response schema validation."""
#         response = client.get(
#             "/api/v1/predict/btc?horizon=invalid",
#             headers={"Authorization": f"Bearer {auth_token}"}
#         )

#         assert response.status_code == 422
#         data = response.json()

#         # Validate error response format
#         assert "detail" in data
#         assert isinstance(data["detail"], str)

#         # Check for validation errors
#         if "errors" in data:
#             assert isinstance(data["errors"], list)
#             for error in data["errors"]:
#                 assert "field" in error
#                 assert "message" in error
#                 assert "type" in error

#     def test_timestamp_format(self, client, auth_token):
#         """Test that all timestamps are in ISO 8601 format."""
#         with patch("app.api.v1.market.market_service.get_prices") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "prices": [
#                     {
#                         "timestamp": datetime.now(timezone.utc).isoformat(),
#                         "price": 45000.00
#                     }
#                 ],
#                 "total": 1,
#                 "limit": 100,
#                 "offset": 0,
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/btc/prices?limit=1",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate timestamp format
#             import re
#             iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?$'

#             assert re.match(iso_pattern, data["timestamp"])
#             for price in data["prices"]:
#                 assert re.match(iso_pattern, price["timestamp"])

#     def test_pagination_response_schema(self, client, auth_token):
#         """Test pagination response schema validation."""
#         with patch("app.api.v1.market.market_service.get_prices") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "prices": [],
#                 "total": 100,
#                 "limit": 10,
#                 "offset": 20,
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/btc/prices?limit=10&offset=20",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate pagination fields
#             assert "total" in data
#             assert "limit" in data
#             assert "offset" in data
#             assert isinstance(data["total"], int)
#             assert isinstance(data["limit"], int)
#             assert isinstance(data["offset"], int)
#             assert data["limit"] == 10
#             assert data["offset"] == 20

#     def test_cached_flag_response(self, client, auth_token):
#         """Test cached flag in response."""
#         with patch("app.api.v1.market.market_service.get_prices") as mock_get:
#             mock_get.return_value = {
#                 "symbol": "BTC",
#                 "prices": [],
#                 "total": 0,
#                 "limit": 100,
#                 "offset": 0,
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "cached": False
#             }

#             response = client.get(
#                 "/api/v1/btc/prices?limit=1",
#                 headers={"Authorization": f"Bearer {auth_token}"}
#             )

#             assert response.status_code == 200
#             data = response.json()

#             # Validate cached flag
#             assert "cached" in data
#             assert isinstance(data["cached"], bool)
#             assert data["cached"] is False