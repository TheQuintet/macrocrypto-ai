"""Test suite for API Gateway service.

This package contains all tests organized by type:

Directory structure:
- unit/: Unit tests for individual components
  - test_auth/: Authentication tests
  - test_cache/: Caching tests
  - test_database/: Database model tests
  - test_routes/: API endpoint tests
  - test_websocket/: WebSocket tests
- integration/: Integration tests with external services
- e2e/: End-to-end workflow tests
- fixtures/: Shared test fixtures and mock data

Run tests with:
    pytest tests/ -v
    pytest tests/unit/ -v
    pytest tests/integration/ -v
    pytest tests/e2e/ -v
"""

# Make pytest see this as a proper test package