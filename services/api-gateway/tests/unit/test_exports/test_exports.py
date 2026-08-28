"""Unit tests for export API endpoints."""

import pytest
import time
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from io import BytesIO

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
def active_user(db_session):
    """Create an active test user with unique email."""
    unique = str(int(time.time() * 1000000))
    user = User(
        email=f"testexport{unique}@example.com",
        username=f"testexport{unique}",
        hashed_password=get_password_hash("TestPass123"),
        full_name="Test Export User",
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


class TestExportsEndpoint:
    """Test export API endpoint."""

    def test_exports_endpoint_unauthenticated(self, client):
        """Test exports endpoint without authentication."""
        response = client.get("/api/v1/export?export_type=predictions&format=csv")
        assert response.status_code == 401
        assert "Not authenticated" in response.text

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_exports_endpoint_csv(self, mock_generate_export, client, access_token):
        """Test CSV export."""
        mock_generate_export.return_value = {
            "file_path": "/exports/test.csv",
            "file_name": "predictions_BTC_24h_20260828_120000.csv",
            "file_size": 2048,
            "content_type": "text/csv",
            "data": b"timestamp,price\n2026-08-28,45000.00\n",
        }

        response = client.get(
            "/api/v1/export?export_type=predictions&format=csv&timeframe=24h",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert response.content == b"timestamp,price\n2026-08-28,45000.00\n"

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_exports_endpoint_png(self, mock_generate_export, client, access_token):
        """Test PNG export."""
        mock_generate_export.return_value = {
            "file_path": "/exports/test.png",
            "file_name": "predictions_BTC_24h_20260828_120000.png",
            "file_size": 4096,
            "content_type": "image/png",
            "data": b"PNG test data",
        }

        response = client.get(
            "/api/v1/export?export_type=predictions&format=png&timeframe=24h",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert response.content == b"PNG test data"

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_exports_endpoint_pdf(self, mock_generate_export, client, access_token):
        """Test PDF export."""
        mock_generate_export.return_value = {
            "file_path": "/exports/test.pdf",
            "file_name": "predictions_BTC_24h_20260828_120000.pdf",
            "file_size": 8192,
            "content_type": "application/pdf",
            "data": b"%PDF test data",
        }

        response = client.get(
            "/api/v1/export?export_type=predictions&format=pdf&timeframe=24h",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert response.content == b"%PDF test data"

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_exports_endpoint_accuracy(self, mock_generate_export, client, access_token):
        """Test accuracy export."""
        mock_generate_export.return_value = {
            "file_path": "/exports/test.csv",
            "file_name": "accuracy_BTC_30_20260828_120000.csv",
            "file_size": 1024,
            "content_type": "text/csv",
            "data": b"Metric,Value\nAccuracy,85.5\n",
        }

        response = client.get(
            "/api/v1/export?export_type=accuracy&format=csv&days=30",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"

    @patch("app.api.v1.exports.export_service.generate_export")
    def test_exports_endpoint_correlations(self, mock_generate_export, client, access_token):
        """Test correlations export."""
        mock_generate_export.return_value = {
            "file_path": "/exports/test.csv",
            "file_name": "correlations_BTC_30d_20260828_120000.csv",
            "file_size": 1024,
            "content_type": "text/csv",
            "data": b"Indicator,Correlation\nS&P500,0.65\n",
        }

        response = client.get(
            "/api/v1/export?export_type=correlations&format=csv&window=30d",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200

    def test_exports_endpoint_invalid_type(self, client, access_token):
        """Test exports with invalid export type."""
        response = client.get(
            "/api/v1/export?export_type=invalid&format=csv",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 422

    def test_exports_endpoint_invalid_format(self, client, access_token):
        """Test exports with invalid format."""
        response = client.get(
            "/api/v1/export?export_type=predictions&format=invalid",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 422


class TestExportHistory:
    """Test export history endpoint."""

    def test_history_endpoint_unauthenticated(self, client):
        """Test history endpoint without authentication."""
        response = client.get("/api/v1/export/history")
        assert response.status_code == 401

    def test_history_endpoint_success(self, client, db_session, active_user, access_token):
        """Test successful history retrieval."""
        # Create some export history records
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
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) == 3
        assert data["total"] == 3

    def test_history_endpoint_pagination(self, client, db_session, active_user, access_token):
        """Test history endpoint with pagination."""
        # Create 5 export history records
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
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["limit"] == 2
        assert data["offset"] == 1
        assert len(data["items"]) == 2


class TestDownloadExport:
    """Test download export endpoint."""

    def test_download_unauthenticated(self, client):
        """Test download without authentication."""
        response = client.get("/api/v1/export/1/download")
        assert response.status_code == 401

    def test_download_not_found(self, client, access_token):
        """Test download with non-existent export ID."""
        response = client.get(
            "/api/v1/export/999/download",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 404

    def test_download_not_completed(self, client, db_session, active_user, access_token):
        """Test download with incomplete export."""
        export = ExportHistory(
            user_id=active_user.id,
            export_type="predictions",
            format="csv",
            status=ExportStatus.PENDING,
        )
        db_session.add(export)
        db_session.commit()

        response = client.get(
            f"/api/v1/export/{export.id}/download",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 400
        assert "not completed" in response.text

    @patch("os.path.exists")
    def test_download_success(self, mock_exists, client, db_session, active_user, access_token):
        """Test successful download."""
        mock_exists.return_value = True

        export = ExportHistory(
            user_id=active_user.id,
            export_type="predictions",
            format="csv",
            status=ExportStatus.COMPLETED,
            file_path="/exports/test.csv",
            file_name="test.csv",
            file_size=1024,
            completed_at=datetime.now(timezone.utc),
        )
        db_session.add(export)
        db_session.commit()

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = mock_open
            mock_open.return_value.__exit__ = MagicMock()
            mock_open.return_value.read.return_value = b"test data"

            response = client.get(
                f"/api/v1/export/{export.id}/download",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            assert response.status_code == 200
            assert response.content == b"test data"
            assert "attachment; filename=test.csv" in response.headers["content-disposition"]

            # Verify download count was incremented
            db_session.refresh(export)
            assert export.download_count == 1