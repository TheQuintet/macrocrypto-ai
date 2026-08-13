# """Pytest fixtures for data-service tests"""

# import pytest
# from fastapi.testclient import TestClient
# from app.main import app
# from app.services.price_service import PriceService
# from app.services.data_processor import DataProcessor


# @pytest.fixture(autouse=True)
# def setup_app_state():
#     """Ensure app.state has required attributes for testing."""
#     # Create a mock data_processor for testing
#     price_service = PriceService()
#     data_processor = DataProcessor(price_service=price_service)
    
#     # Set app state
#     app.state.data_processor = data_processor
#     app.state.price_service = price_service
#     app.state.cache_client = None
#     app.state.rabbitmq_producer = None
    
#     yield
    
#     # Cleanup
#     if hasattr(app.state, 'data_processor'):
#         del app.state.data_processor


# @pytest.fixture
# def client():
#     """Create a test client for FastAPI app."""
#     return TestClient(app)


# @pytest.fixture
# def api_base_url():
#     """Return the base URL for API tests."""
#     return "http://localhost:8001"


# @pytest.fixture
# def price_endpoint(api_base_url):
#     """Return the full price endpoint URL."""
#     return f"{api_base_url}/api/v1/btc/price"

"""Pytest fixtures for data-service tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.price_service import PriceService
from app.services.data_processor import DataProcessor
from app.database.session import SessionLocal


@pytest.fixture(autouse=True)
def setup_app_state():
    """Ensure app.state has required attributes for testing."""

    # Create a mock data_processor for testing
    price_service = PriceService()
    data_processor = DataProcessor(price_service=price_service)

    # Set app state
    app.state.data_processor = data_processor
    app.state.price_service = price_service
    app.state.cache_client = None
    app.state.rabbitmq_producer = None

    yield

    # Cleanup
    if hasattr(app.state, "data_processor"):
        del app.state.data_processor

    if hasattr(app.state, "price_service"):
        del app.state.price_service

    if hasattr(app.state, "cache_client"):
        del app.state.cache_client

    if hasattr(app.state, "rabbitmq_producer"):
        del app.state.rabbitmq_producer


@pytest.fixture
def client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def api_base_url():
    """Return the base URL for API tests."""
    return "http://localhost:8001"


@pytest.fixture
def price_endpoint(api_base_url):
    """Return the full price endpoint URL."""
    return f"{api_base_url}/api/v1/btc/price"


@pytest.fixture
def db():
    """
    Provide a database session for integration tests.

    The session uses the application's configured database
    connection and is rolled back after each test.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()