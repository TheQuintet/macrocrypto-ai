"""Tests for prediction alert API routes."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.prediction_routes import (
    create_prediction_alert,
    get_prediction_alerts,
    get_prediction_alert,
    update_prediction_alert,
    delete_prediction_alert,
    get_prediction_config,
    update_prediction_config,
    get_db,
)
from app.models.prediction_alert import (
    PredictionChangeAlert,
    PredictionChangeConfig,
    PredictionAlertStatus,
    PredictionHorizon,
    PredictionDirection,
)


@pytest.fixture
def db():
    """Provide a mocked database session."""
    return MagicMock()


@pytest.fixture
def user_id():
    """Provide a user UUID."""
    return uuid4()


@pytest.fixture
def alert_id():
    """Provide an alert UUID."""
    return uuid4()


@pytest.fixture
def alert():
    """Provide a mocked prediction alert."""
    item = MagicMock()
    item.id = uuid4()
    item.user_id = uuid4()
    item.created_at = datetime(2026, 1, 1)
    item.to_dict.return_value = {
        "id": str(item.id),
        "user_id": str(item.user_id),
        "threshold_percent": 5.0,
        "status": "active",
    }
    return item


@pytest.fixture
def config():
    """Provide a mocked prediction configuration."""
    item = MagicMock()
    item.to_dict.return_value = {
        "default_threshold": 2.0,
        "confidence_change_threshold": 5.0,
        "default_horizon": "24h",
        "notify_in_app_default": True,
        "notify_email_default": True,
    }
    return item


def mock_query(db, result=None, count=0):
    """Configure a chainable mocked SQLAlchemy query."""
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    query.offset.return_value = query
    query.limit.return_value = query
    query.count.return_value = count
    query.all.return_value = result or []
    query.first.return_value = result
    return query


class TestGetDb:
    """Tests for the database dependency."""

    def test_yields_and_closes_session(self):
        mock_session = MagicMock()

        with patch(
            "app.api.prediction_routes.SessionLocal",
            return_value=mock_session,
        ):
            generator = get_db()

            assert next(generator) is mock_session
            generator.close()

        mock_session.close.assert_called_once_with()

    def test_closes_session_when_generator_finishes(self):
        mock_session = MagicMock()

        with patch(
            "app.api.prediction_routes.SessionLocal",
            return_value=mock_session,
        ):
            generator = get_db()

            assert next(generator) is mock_session

            with pytest.raises(StopIteration):
                next(generator)

        mock_session.close.assert_called_once_with()


class TestCreatePredictionAlert:
    """Tests for creating prediction alerts."""

    @pytest.mark.asyncio
    async def test_create_alert_success(self, db, user_id):
        alert_data = MagicMock()
        alert_data.user_id = user_id
        alert_data.threshold_percent = 5.0
        alert_data.horizon = PredictionHorizon("24h").value
        alert_data.direction = list(PredictionDirection)[0].value
        alert_data.asset = "BTC"
        alert_data.monitor_confidence = True
        alert_data.confidence_threshold_percent = 5.0
        alert_data.name = "BTC alert"
        alert_data.description = "Test alert"
        alert_data.notify_in_app = True
        alert_data.notify_email = False

        query = mock_query(db, count=0)

        with patch(
            "app.api.prediction_routes.settings.MAX_ALERTS_PER_USER",
            10,
        ), patch(
            "app.api.prediction_routes.PredictionChangeAlert"
        ) as model:
            created_alert = MagicMock()
            created_alert.to_dict.return_value = {"id": "new-alert"}
            model.return_value = created_alert

            result = await create_prediction_alert(
                alert_data=alert_data,
                db=db,
            )

        assert result == {"id": "new-alert"}
        model.assert_called_once()
        db.add.assert_called_once_with(created_alert)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(created_alert)

    @pytest.mark.asyncio
    async def test_create_alert_rejects_when_limit_reached(
        self,
        db,
        user_id,
    ):
        alert_data = MagicMock()
        alert_data.user_id = user_id

        mock_query(db, count=10)

        with patch(
            "app.api.prediction_routes.settings.MAX_ALERTS_PER_USER",
            10,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await create_prediction_alert(
                    alert_data=alert_data,
                    db=db,
                )

        assert exc_info.value.status_code == 400
        assert "Maximum alerts per user" in exc_info.value.detail
        db.add.assert_not_called()
        db.commit.assert_not_called()


class TestGetPredictionAlerts:
    """Tests for listing prediction alerts."""

    @pytest.mark.asyncio
    async def test_returns_alerts(self, db, user_id, alert):
        mock_query(db, result=[alert], count=1)

        result = await get_prediction_alerts(
            user_id=user_id,
            status=None,
            horizon=None,
            limit=50,
            offset=0,
            db=db,
        )

        assert result == {
            "total": 1,
            "limit": 50,
            "offset": 0,
            "alerts": [alert.to_dict.return_value],
        }

    @pytest.mark.asyncio
    async def test_returns_empty_list(self, db, user_id):
        mock_query(db, result=[], count=0)

        result = await get_prediction_alerts(
            user_id=user_id,
            status=None,
            horizon=None,
            limit=50,
            offset=0,
            db=db,
        )

        assert result == {
            "total": 0,
            "limit": 50,
            "offset": 0,
            "alerts": [],
        }

    @pytest.mark.asyncio
    async def test_applies_pagination(self, db, user_id, alert):
        query = mock_query(db, result=[alert], count=25)

        result = await get_prediction_alerts(
            user_id=user_id,
            status=None,
            horizon=None,
            limit=10,
            offset=5,
            db=db,
        )

        query.offset.assert_called_once_with(5)
        query.limit.assert_called_once_with(10)
        assert result["total"] == 25
        assert result["limit"] == 10
        assert result["offset"] == 5

    @pytest.mark.asyncio
    async def test_filters_by_valid_status(self, db, user_id):
        query = mock_query(db, result=[], count=0)
        valid_status = list(PredictionAlertStatus)[0].value

        await get_prediction_alerts(
            user_id=user_id,
            status=valid_status,
            horizon=None,
            limit=50,
            offset=0,
            db=db,
        )

        assert query.filter.call_count == 2

    @pytest.mark.asyncio
    async def test_filters_by_valid_horizon(self, db, user_id):
        query = mock_query(db, result=[], count=0)
        valid_horizon = list(PredictionHorizon)[0].value

        await get_prediction_alerts(
            user_id=user_id,
            status=None,
            horizon=valid_horizon,
            limit=50,
            offset=0,
            db=db,
        )

        assert query.filter.call_count == 2


class TestGetPredictionAlert:
    """Tests for retrieving one prediction alert."""

    @pytest.mark.asyncio
    async def test_returns_alert_when_found(self, db, alert_id, alert):
        mock_query(db, result=alert)

        result = await get_prediction_alert(
            alert_id=alert_id,
            db=db,
        )

        assert result == alert.to_dict.return_value

    @pytest.mark.asyncio
    async def test_raises_404_when_missing(self, db, alert_id):
        mock_query(db, result=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_prediction_alert(
                alert_id=alert_id,
                db=db,
            )

        assert exc_info.value.status_code == 404
        assert str(alert_id) in exc_info.value.detail


class TestUpdatePredictionAlert:
    """Tests for updating prediction alerts."""

    @pytest.mark.asyncio
    async def test_update_alert_success(self, db, alert_id, alert):
        mock_query(db, result=alert)

        update_data = MagicMock()
        update_data.model_dump.return_value = {
            "threshold_percent": 8.0,
            "name": "Updated alert",
            "notify_email": True,
        }

        result = await update_prediction_alert(
            alert_id=alert_id,
            alert_data=update_data,
            db=db,
        )

        assert alert.threshold_percent == 8.0
        assert alert.name == "Updated alert"
        assert alert.notify_email is True
        assert isinstance(alert.updated_at, datetime)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(alert)
        assert result == alert.to_dict.return_value

    @pytest.mark.asyncio
    async def test_update_alert_with_empty_data(
        self,
        db,
        alert_id,
        alert,
    ):
        mock_query(db, result=alert)

        update_data = MagicMock()
        update_data.model_dump.return_value = {}

        await update_prediction_alert(
            alert_id=alert_id,
            alert_data=update_data,
            db=db,
        )

        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(alert)

    @pytest.mark.asyncio
    async def test_update_alert_not_found(self, db, alert_id):
        mock_query(db, result=None)

        update_data = MagicMock()
        update_data.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await update_prediction_alert(
                alert_id=alert_id,
                alert_data=update_data,
                db=db,
            )

        assert exc_info.value.status_code == 404
        db.commit.assert_not_called()


class TestDeletePredictionAlert:
    """Tests for deleting prediction alerts."""

    @pytest.mark.asyncio
    async def test_delete_alert_success(self, db, alert_id, alert):
        mock_query(db, result=alert)

        result = await delete_prediction_alert(
            alert_id=alert_id,
            db=db,
        )

        assert result is None
        db.delete.assert_called_once_with(alert)
        db.commit.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_delete_alert_not_found(self, db, alert_id):
        mock_query(db, result=None)

        with pytest.raises(HTTPException) as exc_info:
            await delete_prediction_alert(
                alert_id=alert_id,
                db=db,
            )

        assert exc_info.value.status_code == 404
        db.delete.assert_not_called()
        db.commit.assert_not_called()


class TestGetPredictionConfig:
    """Tests for retrieving prediction alert configuration."""

    @pytest.mark.asyncio
    async def test_returns_existing_config(self, db, user_id, config):
        mock_query(db, result=config)

        result = await get_prediction_config(
            user_id=user_id,
            db=db,
        )

        assert result == config.to_dict.return_value

    @pytest.mark.asyncio
    async def test_returns_defaults_when_config_missing(
        self,
        db,
        user_id,
    ):
        mock_query(db, result=None)

        result = await get_prediction_config(
            user_id=user_id,
            db=db,
        )

        assert result == {
            "user_id": str(user_id),
            "default_threshold": 2.0,
            "confidence_change_threshold": 5.0,
            "default_horizon": "24h",
            "notify_in_app_default": True,
            "notify_email_default": True,
        }


class TestUpdatePredictionConfig:
    """Tests for updating prediction alert configuration."""

    @pytest.mark.asyncio
    async def test_updates_existing_config(self, db, user_id, config):
        mock_query(db, result=config)

        update_data = MagicMock()
        update_data.model_dump.return_value = {
            "default_threshold": 3.5,
            "notify_email_default": False,
        }

        result = await update_prediction_config(
            user_id=user_id,
            config_data=update_data,
            db=db,
        )

        assert config.default_threshold == 3.5
        assert config.notify_email_default is False
        assert isinstance(config.updated_at, datetime)
        db.add.assert_not_called()
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(config)
        assert result == config.to_dict.return_value

    @pytest.mark.asyncio
    async def test_creates_config_when_missing(self, db, user_id):
        mock_query(db, result=None)

        update_data = MagicMock()
        update_data.model_dump.return_value = {
            "default_threshold": 4.0,
        }

        with patch(
            "app.api.prediction_routes.PredictionChangeConfig"
        ) as model:
            new_config = MagicMock()
            new_config.to_dict.return_value = {
                "default_threshold": 4.0,
            }
            model.return_value = new_config

            result = await update_prediction_config(
                user_id=user_id,
                config_data=update_data,
                db=db,
            )

        model.assert_called_once_with(user_id=user_id)
        db.add.assert_called_once_with(new_config)
        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(new_config)
        assert result == {"default_threshold": 4.0}

    @pytest.mark.asyncio
    async def test_updates_config_with_empty_data(
        self,
        db,
        user_id,
        config,
    ):
        mock_query(db, result=config)

        update_data = MagicMock()
        update_data.model_dump.return_value = {}

        await update_prediction_config(
            user_id=user_id,
            config_data=update_data,
            db=db,
        )

        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(config)