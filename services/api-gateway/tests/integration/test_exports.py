"""Integration tests for exports endpoints."""

import pytest
import time
import os
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User, UserStatus, UserRole
from app.models.export_history import ExportHistory, ExportStatus
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
def auth_token_and_user(client, db_session):
    """Create a user and return both auth token and user object."""
    import time
    unique = str(int(time.time() * 1000000))
    username = f"exportuser{unique}"
    email = f"export{unique}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "TestPass123",
            "full_name": "Export User"
        }
    )
    user_id = register_response.json()["id"]

    user = db_session.query(User).filter(User.id == user_id).first()
    user.status = UserStatus.ACTIVE
    user.is_email_verified = True
    db_session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": "TestPass123"
        }
    )
    token = login_response.json()["access_token"]

    return {"token": token, "user": user}


@pytest.fixture
def auth_token(auth_token_and_user):
    """Return auth token."""
    return auth_token_and_user["token"]


@pytest.fixture
def active_user(auth_token_and_user):
    """Return the user object from auth_token_and_user fixture."""
    return auth_token_and_user["user"]


class TestExportsIntegration:
    """Integration tests for exports endpoints."""

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_export_csv(self, mock_generate_export, client, auth_token):
        """Test CSV export."""
        mock_generate_export.return_value = {
            "file_path": "/tmp/test.csv",
            "file_name": "predictions_BTC_24h_20260828_120000.csv",
            "file_size": 1633,
            "content_type": "text/csv",
            "data": b"timestamp,price\n2026-08-28,45000.00\n"
        }

        response = client.get(
            "/api/v1/export?export_type=predictions&format=csv&timeframe=24h",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert response.content == b"timestamp,price\n2026-08-28,45000.00\n"

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_export_png(self, mock_generate_export, client, auth_token):
        """Test PNG export."""
        mock_generate_export.return_value = {
            "file_path": "/tmp/test.png",
            "file_name": "predictions_BTC_24h_20260828_120000.png",
            "file_size": 59779,
            "content_type": "image/png",
            "data": b"PNG test data"
        }

        response = client.get(
            "/api/v1/export?export_type=predictions&format=png&timeframe=24h",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert "image/png" in response.headers["content-type"]
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert response.content == b"PNG test data"

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_export_pdf(self, mock_generate_export, client, auth_token):
        """Test PDF export."""
        mock_generate_export.return_value = {
            "file_path": "/tmp/test.pdf",
            "file_name": "predictions_BTC_24h_20260828_120000.pdf",
            "file_size": 84455,
            "content_type": "application/pdf",
            "data": b"%PDF test data"
        }

        response = client.get(
            "/api/v1/export?export_type=predictions&format=pdf&timeframe=24h",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert "application/pdf" in response.headers["content-type"]
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert response.content == b"%PDF test data"

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_export_accuracy(self, mock_generate_export, client, auth_token):
        """Test accuracy export."""
        mock_generate_export.return_value = {
            "file_path": "/tmp/test.csv",
            "file_name": "accuracy_BTC_30_20260828_120000.csv",
            "file_size": 1024,
            "content_type": "text/csv",
            "data": b"Metric,Value\nAccuracy,85.5\n"
        }

        response = client.get(
            "/api/v1/export?export_type=accuracy&format=csv&days=30",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_invalid_type(self, client, auth_token):
        """Test export with invalid export type."""
        response = client.get(
            "/api/v1/export?export_type=invalid&format=csv",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_export_invalid_format(self, client, auth_token):
        """Test export with invalid format."""
        response = client.get(
            "/api/v1/export?export_type=predictions&format=invalid",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_export_history(self, client, db_session, auth_token, active_user):
        """Test export history."""
        # Create some export history records for the same user
        for i in range(3):
            export = ExportHistory(
                user_id=active_user.id,
                export_type="predictions",
                format="csv",
                status=ExportStatus.COMPLETED,
                file_name=f"test_{i}.csv",
                file_size=1024,
                completed_at=datetime.now(timezone.utc),
            )
            db_session.add(export)
        db_session.commit()

        response = client.get(
            "/api/v1/export/history?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) == 3

    def test_export_history_pagination(self, client, db_session, auth_token, active_user):
        """Test export history with pagination."""
        # Create 5 export history records for the same user
        for i in range(5):
            export = ExportHistory(
                user_id=active_user.id,
                export_type="predictions",
                format="csv",
                status=ExportStatus.COMPLETED,
                file_name=f"test_{i}.csv",
                file_size=1024,
                completed_at=datetime.now(timezone.utc),
            )
            db_session.add(export)
        db_session.commit()

        response = client.get(
            "/api/v1/export/history?limit=2&offset=1",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 1
        assert len(data["items"]) == 2

    def test_download_not_found(self, client, auth_token):
        """Test download with non-existent export ID."""
        response = client.get(
            "/api/v1/export/999/download",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_export_unauthenticated(self, client):
        """Test export endpoint without authentication."""
        response = client.get("/api/v1/export?export_type=predictions&format=csv")
        assert response.status_code == 401

    def test_history_unauthenticated(self, client):
        """Test history endpoint without authentication."""
        response = client.get("/api/v1/export/history")
        assert response.status_code == 401