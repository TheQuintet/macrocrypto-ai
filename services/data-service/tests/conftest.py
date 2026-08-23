"""Pytest fixtures for data-service tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.price_service import PriceService
from app.services.data_processor import DataProcessor
from app.database.session import SessionLocal


@pytest.fixture(autouse=True)
def setup_app_state():
    """
    Ensure app.state has required attributes for testing.
    """

    price_service = PriceService()

    data_processor = DataProcessor(
        price_service=price_service
    )

    app.state.data_processor = data_processor
    app.state.price_service = price_service
    app.state.cache_client = None
    app.state.rabbitmq_producer = None

    yield

    for attr in [
        "data_processor",
        "price_service",
        "cache_client",
        "rabbitmq_producer",
    ]:
        if hasattr(app.state, attr):
            delattr(app.state, attr)


@pytest.fixture
def client():
    """
    FastAPI test client.
    """

    return TestClient(app)


@pytest.fixture
def api_base_url():
    return "http://localhost:8001"


@pytest.fixture
def price_endpoint(api_base_url):
    return f"{api_base_url}/api/v1/btc/price"


@pytest.fixture
def db():
    """
    Application database session.
    """

    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


@pytest.fixture
def clean_db():
    """
    Clean economic calendar tables before each test.
    """

    from app.models.economic_event import EconomicEvent
    from app.models.user_calendar_preference import UserCalendarPreference

    session = SessionLocal()

    try:

        session.query(EconomicEvent).delete()

        session.query(UserCalendarPreference).delete()

        session.commit()

        yield session

    finally:

        session.rollback()
        session.close()