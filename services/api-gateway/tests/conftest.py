# ============================================
# IMPORTS & DATABASE SETUP
# ============================================
import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv
from sqlalchemy.orm import Session, sessionmaker
# Import app components after environment variables are set
from app.main import app
from app.models.base import Base
from app.models.user import User, UserStatus, UserRole
from app.core.database import get_db, create_database_engine, SessionLocal  # Import from your module

# Force set TESTING mode BEFORE importing app
os.environ["TESTING"] = "true"

# Add the parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

# Use PostgreSQL if DATABASE_URL is provided (CI / Docker), 
# otherwise fall back to SQLite for local development
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./test.db"
)

# Temporarily override environment DATABASE_URL so app/database.py picks it up if needed
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


# from app.api.deps import get_db  # Update if your get_db is located elsewhere
# Create test engine using your project's create_database_engine function
engine = create_database_engine()

# Test session maker
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ============================================
# DATABASE & CLIENT FIXTURES
# ============================================

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Automatically create tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(setup_database) -> Generator[Session, None, None]:
    """
    Create a new database session for a test.

    Yields:
        Session: SQLAlchemy session for the test.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    Create a TestClient instance for the FastAPI application with 
    database dependency overrides so API requests use the test engine.
    """
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override app's database dependency
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides after session
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def app_instance():
    """Return the FastAPI application instance."""
    return app


@pytest.fixture
def test_env() -> dict:
    """Return a copy of the current environment variables."""
    return dict(os.environ)


# ============================================
# PYTEST CONFIGURATION
# ============================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
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
# USER & AUTH FIXTURES
# ============================================

@pytest.fixture
def test_user(db_session):
    """Create a test user (pending status)."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password",
        full_name="Test User",
        role=UserRole.USER,
        status=UserStatus.PENDING,
        is_email_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def active_user(db_session):
    """Create an active test user."""
    from app.core.security import get_password_hash
    user = User(
        email="active@example.com",
        username="activeuser",
        hashed_password=get_password_hash("TestPass123"),
        full_name="Active User",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
        is_email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def active_user_token(client, active_user):
    """Get an access token for the active user."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "activeuser",
            "password": "TestPass123"
        }
    )
    return response.json()["access_token"]

@pytest.fixture
def active_user_refresh_token(client, active_user):
    """Get a refresh token for the active user."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "activeuser",
            "password": "TestPass123"
        }
    )
    return response.json()["refresh_token"]


# ============================================
# CLEANUP
# ============================================

# Optional: Add cleanup after all tests
# def pytest_sessionfinish(session):
#     """Clean up after all tests complete."""
#     pass