"""Tests for database connection and session management."""

import pytest
from sqlalchemy import text

from app.core.database import engine, SessionLocal, check_database_health, get_database_status


class TestDatabaseConnection:
    """Test database connection and session management."""

    def test_engine_created(self):
        """Test that database engine is created."""
        assert engine is not None
        # Test that we can connect
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1

    def test_session_creation(self):
        """Test that a session can be created."""
        db = SessionLocal()
        try:
            assert db is not None
            # Test that we can execute a query
            result = db.execute(text("SELECT 1")).scalar()
            assert result == 1
        finally:
            db.close()

    def test_database_health_check(self):
        """Test database health check."""
        # Should work with our test database
        assert check_database_health() is True

    def test_database_status(self):
        """Test database status information."""
        status = get_database_status()
        assert "connected" in status
        # For SQLite, version might not be available
        # Just check that it returns something
        assert isinstance(status, dict)