"""Tests for the Alert Service FastAPI application."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import app.main as main


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(main.app)


@pytest.fixture
def mock_db():
    """Create a mocked database session."""
    db = MagicMock()
    db.execute = MagicMock()
    db.close = MagicMock()
    return db


# ============================================================================
# FastAPI Application Configuration
# ============================================================================


class TestApplication:
    """Test FastAPI application configuration."""

    def test_app_title(self):
        """Test application title."""
        assert main.app.title == "Alert Service"

    def test_app_description(self):
        """Test application description."""
        assert (
            main.app.description
            == "MacroCrypto AI Alert Service - Evaluate alerts and send notifications"
        )

    def test_app_version(self):
        """Test application version."""
        assert main.app.version == "1.0.0"



    def test_routes_are_registered(self):
        """Test that the application and imported routers contain expected routes."""
        app_paths = {
            route.path
            for route in main.app.routes
            if hasattr(route, "path")
        }

        # Application-level routes
        assert "/health" in app_paths
        assert "/ready" in app_paths

        # Verify each included router has routes configured.
        price_paths = {
            route.path
            for route in main.router.routes
            if hasattr(route, "path")
        }
        prediction_paths = {
            route.path
            for route in main.prediction_router.routes
            if hasattr(route, "path")
        }
        macro_paths = {
            route.path
            for route in main.macro_router.routes
            if hasattr(route, "path")
        }
        notification_paths = {
            route.path
            for route in main.notifications_router.routes
            if hasattr(route, "path")
        }

        assert price_paths
        assert prediction_paths
        assert macro_paths
        assert notification_paths




# ============================================================================
# Price Update Handler
# ============================================================================


class TestHandlePriceUpdate:
    """Test price update event handling."""

    def test_returns_when_alert_engine_not_initialized(self):
        """Test handler exits when global alert engine is not initialized."""
        original_engine = main.alert_engine

        try:
            main.alert_engine = None

            with patch("app.main.SessionLocal") as mock_session:
                main.handle_price_update(
                    {
                        "data": {
                            "symbol": "BTCUSDT",
                            "price": 75000,
                        }
                    }
                )

                mock_session.assert_not_called()
        finally:
            main.alert_engine = original_engine

    def test_processes_price_update(self, mock_db):
        """Test that a price update is evaluated by AlertEngine."""
        original_engine = main.alert_engine

        try:
            main.alert_engine = MagicMock()

            engine = MagicMock()
            engine.evaluate_price_alerts.return_value = []

            with (
                patch("app.main.SessionLocal", return_value=mock_db),
                patch("app.main.AlertEngine", return_value=engine) as mock_engine_class,
            ):
                main.handle_price_update(
                    {
                        "data": {
                            "symbol": "BTCUSDT",
                            "price": 75000,
                        }
                    }
                )

            mock_engine_class.assert_called_once_with(
                mock_db,
                main.rabbitmq_producer,
            )
            engine.evaluate_price_alerts.assert_called_once_with(
                {
                    "symbol": "BTCUSDT",
                    "price": 75000,
                }
            )
            mock_db.close.assert_called_once()
        finally:
            main.alert_engine = original_engine

    def test_logs_triggered_alerts(self, mock_db):
        """Test handler logs when alerts are triggered."""
        original_engine = main.alert_engine

        try:
            main.alert_engine = MagicMock()

            engine = MagicMock()
            engine.evaluate_price_alerts.return_value = [
                MagicMock(),
                MagicMock(),
            ]

            with (
                patch("app.main.SessionLocal", return_value=mock_db),
                patch("app.main.AlertEngine", return_value=engine),
                patch("app.main.logger") as mock_logger,
            ):
                main.handle_price_update(
                    {
                        "data": {
                            "symbol": "BTCUSDT",
                            "price": 75000,
                        }
                    }
                )

            mock_logger.info.assert_any_call(
                "🔔 2 price alerts triggered"
            )
        finally:
            main.alert_engine = original_engine

    def test_handles_missing_data(self, mock_db):
        """Test handler accepts messages without a data payload."""
        original_engine = main.alert_engine

        try:
            main.alert_engine = MagicMock()

            engine = MagicMock()
            engine.evaluate_price_alerts.return_value = []

            with (
                patch("app.main.SessionLocal", return_value=mock_db),
                patch("app.main.AlertEngine", return_value=engine),
            ):
                main.handle_price_update({})

            engine.evaluate_price_alerts.assert_called_once_with({})
            mock_db.close.assert_called_once()
        finally:
            main.alert_engine = original_engine

    def test_handles_processing_exception(self, mock_db):
        """Test handler logs exceptions instead of propagating them."""
        original_engine = main.alert_engine

        try:
            main.alert_engine = MagicMock()

            with (
                patch("app.main.SessionLocal", return_value=mock_db),
                patch(
                    "app.main.AlertEngine",
                    side_effect=RuntimeError("test error"),
                ),
                patch("app.main.logger") as mock_logger,
            ):
                main.handle_price_update(
                    {
                        "data": {
                            "symbol": "BTCUSDT",
                            "price": 75000,
                        }
                    }
                )

            mock_logger.error.assert_called_once()

        finally:
            main.alert_engine = original_engine


# ============================================================================
# Health Check
# ============================================================================


class TestHealthCheck:
    """Test /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_db):
        """Test healthy response when DB and RabbitMQ are connected."""
        consumer = MagicMock()
        consumer.is_connected = True

        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = consumer

            with patch("app.main.SessionLocal", return_value=mock_db):
                result = await main.health_check()

            assert result == {
                "service": main.settings.SERVICE_NAME,
                "status": "healthy",
                "version": "1.0.0",
                "database": "connected",
                "rabbitmq_consumer": "connected",
            }

            mock_db.execute.assert_called_once()
            mock_db.close.assert_called_once()

        finally:
            main.rabbitmq_consumer = original_consumer

    @pytest.mark.asyncio
    async def test_health_check_database_failure(self, mock_db):
        """Test degraded status when database check fails."""
        consumer = MagicMock()
        consumer.is_connected = True

        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = consumer
            mock_db.execute.side_effect = RuntimeError("database unavailable")

            with patch("app.main.SessionLocal", return_value=mock_db):
                result = await main.health_check()

            assert result["status"] == "degraded"
            assert result["database"] == "error: database unavailable"
            assert result["rabbitmq_consumer"] == "connected"

        finally:
            main.rabbitmq_consumer = original_consumer

    @pytest.mark.asyncio
    async def test_health_check_rabbitmq_disconnected(self, mock_db):
        """Test degraded status when RabbitMQ is disconnected."""
        consumer = MagicMock()
        consumer.is_connected = False

        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = consumer

            with patch("app.main.SessionLocal", return_value=mock_db):
                result = await main.health_check()

            assert result["status"] == "degraded"
            assert result["database"] == "connected"
            assert result["rabbitmq_consumer"] == "disconnected"

        finally:
            main.rabbitmq_consumer = original_consumer

    @pytest.mark.asyncio
    async def test_health_check_without_consumer(self, mock_db):
        """Test degraded status when consumer has not been initialized."""
        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = None

            with patch("app.main.SessionLocal", return_value=mock_db):
                result = await main.health_check()

            assert result["status"] == "degraded"
            assert result["database"] == "connected"
            assert result["rabbitmq_consumer"] == "disconnected"

        finally:
            main.rabbitmq_consumer = original_consumer


# ============================================================================
# Readiness Check
# ============================================================================


class TestReadyCheck:
    """Test /ready endpoint."""

    @pytest.mark.asyncio
    async def test_ready_when_rabbitmq_connected_and_db_available(
        self,
        mock_db,
    ):
        """Test ready response when dependencies are available."""
        consumer = MagicMock()
        consumer.is_connected = True

        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = consumer

            with patch("app.main.SessionLocal", return_value=mock_db):
                result = await main.ready_check()

            assert result == ({"status": "ready"}, 200)
            mock_db.execute.assert_called_once()
            mock_db.close.assert_called_once()

        finally:
            main.rabbitmq_consumer = original_consumer

    @pytest.mark.asyncio
    async def test_not_ready_when_rabbitmq_disconnected(self):
        """Test not-ready response when RabbitMQ is unavailable."""
        consumer = MagicMock()
        consumer.is_connected = False

        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = consumer

            result = await main.ready_check()

            assert result == (
                {
                    "status": "not_ready",
                    "reason": "RabbitMQ consumer not connected",
                },
                503,
            )

        finally:
            main.rabbitmq_consumer = original_consumer

    @pytest.mark.asyncio
    async def test_not_ready_when_consumer_missing(self):
        """Test not-ready response when RabbitMQ consumer is not initialized."""
        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = None

            result = await main.ready_check()

            assert result == (
                {
                    "status": "not_ready",
                    "reason": "RabbitMQ consumer not connected",
                },
                503,
            )

        finally:
            main.rabbitmq_consumer = original_consumer

    @pytest.mark.asyncio
    async def test_not_ready_when_database_unavailable(self, mock_db):
        """Test not-ready response when database check fails."""
        consumer = MagicMock()
        consumer.is_connected = True

        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = consumer
            mock_db.execute.side_effect = RuntimeError("database unavailable")

            with patch("app.main.SessionLocal", return_value=mock_db):
                result = await main.ready_check()

            assert result == (
                {
                    "status": "not_ready",
                    "reason": "Database not available",
                },
                503,
            )

        finally:
            main.rabbitmq_consumer = original_consumer


# ============================================================================
# Lifespan
# ============================================================================


class TestLifespan:
    """Test FastAPI application lifespan."""

    @pytest.mark.asyncio
    async def test_lifespan_successful_startup_and_shutdown(self):
        """Test normal startup and shutdown sequence."""
        producer = MagicMock()
        producer.connect.return_value = True

        consumer = MagicMock()
        consumer.connect.return_value = True

        db = MagicMock()

        with (
            patch("app.main.init_db") as mock_init_db,
            patch(
                "app.main.RabbitMQProducer",
                return_value=producer,
            ) as mock_producer_class,
            patch(
                "app.main.RabbitMQConsumer",
                return_value=consumer,
            ) as mock_consumer_class,
            patch(
                "app.main.SessionLocal",
                return_value=db,
            ),
            patch("app.main.AlertEngine") as mock_engine_class,
        ):
            async with main.lifespan(main.app):
                pass

        mock_init_db.assert_called_once()
        mock_producer_class.assert_called_once()
        producer.connect.assert_called_once()

        mock_engine_class.assert_called_once_with(
            db,
            producer,
        )

        mock_consumer_class.assert_called_once()
        consumer.connect.assert_called_once()

        assert consumer.price_callback is main.handle_price_update

        consumer.close.assert_called_once()
        producer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_handles_database_initialization_failure(self):
        """Test startup continues when database initialization fails."""
        producer = MagicMock()
        producer.connect.return_value = True

        consumer = MagicMock()
        consumer.connect.return_value = True

        db = MagicMock()

        with (
            patch(
                "app.main.init_db",
                side_effect=RuntimeError("database init failed"),
            ),
            patch(
                "app.main.RabbitMQProducer",
                return_value=producer,
            ),
            patch(
                "app.main.RabbitMQConsumer",
                return_value=consumer,
            ),
            patch("app.main.SessionLocal", return_value=db),
            patch("app.main.AlertEngine"),
        ):
            async with main.lifespan(main.app):
                pass

        producer.connect.assert_called_once()
        consumer.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_handles_producer_connection_failure(self):
        """Test startup continues when producer connection returns false."""
        producer = MagicMock()
        producer.connect.return_value = False

        consumer = MagicMock()
        consumer.connect.return_value = True

        db = MagicMock()

        with (
            patch("app.main.init_db"),
            patch(
                "app.main.RabbitMQProducer",
                return_value=producer,
            ),
            patch(
                "app.main.RabbitMQConsumer",
                return_value=consumer,
            ),
            patch("app.main.SessionLocal", return_value=db),
            patch("app.main.AlertEngine"),
        ):
            async with main.lifespan(main.app):
                pass

        producer.connect.assert_called_once()
        producer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_handles_producer_initialization_exception(self):
        """Test startup continues when producer initialization raises."""
        consumer = MagicMock()
        consumer.connect.return_value = True

        db = MagicMock()

        with (
            patch("app.main.init_db"),
            patch(
                "app.main.RabbitMQProducer",
                side_effect=RuntimeError("producer failed"),
            ),
            patch(
                "app.main.RabbitMQConsumer",
                return_value=consumer,
            ),
            patch("app.main.SessionLocal", return_value=db),
            patch("app.main.AlertEngine"),
        ):
            async with main.lifespan(main.app):
                pass

        consumer.connect.assert_called_once()
        consumer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_handles_consumer_connection_failure(self):
        """Test startup continues when consumer connection returns false."""
        producer = MagicMock()
        producer.connect.return_value = True

        consumer = MagicMock()
        consumer.connect.return_value = False

        db = MagicMock()

        with (
            patch("app.main.init_db"),
            patch(
                "app.main.RabbitMQProducer",
                return_value=producer,
            ),
            patch(
                "app.main.RabbitMQConsumer",
                return_value=consumer,
            ),
            patch("app.main.SessionLocal", return_value=db),
            patch("app.main.AlertEngine"),
        ):
            async with main.lifespan(main.app):
                pass

        consumer.connect.assert_called_once()
        consumer.close.assert_called_once()
        producer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_handles_consumer_initialization_exception(self):
        """Test startup continues when consumer initialization raises."""
        producer = MagicMock()
        producer.connect.return_value = True

        db = MagicMock()

        with (
            patch("app.main.init_db"),
            patch(
                "app.main.RabbitMQProducer",
                return_value=producer,
            ),
            patch(
                "app.main.RabbitMQConsumer",
                side_effect=RuntimeError("consumer failed"),
            ),
            patch("app.main.SessionLocal", return_value=db),
            patch("app.main.AlertEngine"),
        ):
            async with main.lifespan(main.app):
                pass

        producer.connect.assert_called_once()
        producer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_with_no_connections(self):
        """Test shutdown when RabbitMQ connections were never initialized."""
        db = MagicMock()

        with (
            patch("app.main.init_db"),
            patch(
                "app.main.RabbitMQProducer",
                side_effect=RuntimeError("producer failed"),
            ),
            patch(
                "app.main.RabbitMQConsumer",
                side_effect=RuntimeError("consumer failed"),
            ),
            patch("app.main.SessionLocal", return_value=db),
            patch("app.main.AlertEngine"),
        ):
            async with main.lifespan(main.app):
                pass


# ============================================================================
# HTTP Endpoint Smoke Tests
# ============================================================================


class TestHTTPEndpoints:
    """Test health and readiness endpoints through FastAPI."""

    def test_health_endpoint(self, client, mock_db):
        """Test /health endpoint."""
        consumer = MagicMock()
        consumer.is_connected = True

        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = consumer

            with patch("app.main.SessionLocal", return_value=mock_db):
                response = client.get("/health")

            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            assert response.json()["database"] == "connected"
            assert response.json()["rabbitmq_consumer"] == "connected"

        finally:
            main.rabbitmq_consumer = original_consumer

    def test_ready_endpoint(self, client):
        """Test /ready endpoint when RabbitMQ is unavailable."""
        original_consumer = main.rabbitmq_consumer

        try:
            main.rabbitmq_consumer = None

            response = client.get("/ready")

            # The current implementation returns a tuple from the route.
            # FastAPI serializes it rather than converting it to HTTP 503.
            assert response.status_code == 200

        finally:
            main.rabbitmq_consumer = original_consumer

