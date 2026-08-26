"""Test configuration and shared fixtures for API Gateway tests.

This file provides pytest fixtures and test setup that are automatically
available to all test modules in the tests/ directory.
"""

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# ============================================
# ENVIRONMENT SETUP - MUST BE FIRST
# ============================================

# Force set TESTING mode BEFORE importing app
os.environ["TESTING"] = "true"

# Add the parent directory to path so we can import app
# This ensures tests can run from any directory
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================
# ENVIRONMENT SETUP
# ============================================

# Load .env file from the api-gateway directory
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback: try loading from current directory
    load_dotenv()

# Ensure SECRET_KEY is set for tests
# This prevents validation errors even if .env is missing
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

# Set test mode flag
os.environ["TESTING"] = "true"

# ============================================
# DATABASE FOR TESTS
# ============================================

# Use an in-memory SQLite database for tests
# This avoids the need for a real PostgreSQL database during testing
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ============================================
# IMPORT APP AFTER ENV SETUP
# ============================================

# Import app after environment is set up
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a new database session for a test.

    This fixture creates a fresh database for each test function,
    ensuring tests are isolated and repeatable.

    Yields:
        Session: SQLAlchemy session for the test.
    """
    # Create all tables before the test
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after the test to ensure isolation
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    Create a TestClient instance for the FastAPI application.

    This fixture is available to all test functions.
    It's session-scoped, so it's created once per test session.

    Yields:
        TestClient: A test client for making requests to the app.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def app_instance():
    """
    Return the FastAPI application instance.

    Useful for tests that need to inspect app configuration.

    Returns:
        FastAPI: The FastAPI application instance.
    """
    return app


@pytest.fixture
def test_env() -> dict:
    """
    Return a copy of the current environment variables.

    Useful for tests that need to check environment settings.

    Returns:
        dict: A copy of os.environ.
    """
    return dict(os.environ)


# ============================================
# PYTEST CONFIGURATION
# ============================================

def pytest_configure(config):
    """
    Configure pytest with custom markers.

    This runs automatically when pytest starts.
    """
    config.addinivalue_line(
        "markers",
        "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests (requires DB/Redis/RabbitMQ)"
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests (full flow)"
    )
    config.addinivalue_line(
        "markers",
        "slow: Slow running tests"
    )


# ============================================
# CLEANUP
# ============================================

# Optional: Add cleanup after all tests
# def pytest_sessionfinish(session):
#     """Clean up after all tests complete."""
#     pass