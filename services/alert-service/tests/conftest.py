import os
import sys
from pathlib import Path
from uuid import uuid4
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# ============================================
# ENVIRONMENT SETUP - MUST BE FIRST
# ============================================
os.environ["TESTING"] = "true"

# Add the parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file from the alert-service directory
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

# Use PostgreSQL if DATABASE_URL is provided (CI / Docker), 
# otherwise fall back to SQLite for local development
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_alert.db")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# ============================================
# APP & DATABASE IMPORTS
# ============================================
from app.main import app
from app.models.alert import Base, PriceAlert, AlertType, AlertStatus
from app.database.session import engine, SessionLocal


# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Create all tables in the database once per test session 
    and drop them when the test suite finishes.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Provide a fresh, isolated database session for each test function.
    Rolls back any changes after the test completes so tests remain independent.
    """
    connection = engine.connect()
    transaction = connection.begin()

    session = SessionLocal(bind=connection)

    yield session

    session.close()

    if transaction.is_active:
        transaction.rollback()

    connection.close()


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """
    Create a TestClient instance for the alert-service application with 
    database dependency overrides so API requests use the test engine.
    """
    # Define a local dependency generator for testing
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Try to find and override whatever get_db dependency your routers use,
    # or look for common dependency paths.
    try:
        from app.database.session import SessionLocal as get_db
        app.dependency_overrides[get_db] = override_get_db
    except ImportError:
        try:
            from app.database.session import SessionLocal as get_db
            app.dependency_overrides[get_db] = override_get_db
        except ImportError:
            # If your app defines get_db directly in another module, import it there,
            # or skip overriding if routes manage sessions manually.
            pass

    with TestClient(app) as test_client:
        yield test_client

    if hasattr(app, "dependency_overrides"):
        app.dependency_overrides.clear()


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return uuid4()


@pytest.fixture
def sample_alert_id(db_session: Session, sample_user_id):
    """
    Sample alert ID that pre-creates a valid PriceAlert in the DB 
    to satisfy foreign key constraints.
    """
    alert_id = uuid4()

    price_alert = PriceAlert(
        id=alert_id,
        user_id=sample_user_id,
        threshold_price=85000.0,
        alert_type=AlertType.REACHES,
        asset="BTC/USD",
        status=AlertStatus.ACTIVE,
        one_time=True,
        notify_in_app=True,
        notify_email=True,
        name="Test Price Alert"
    )

    db_session.add(price_alert)
    db_session.commit()

    return alert_id