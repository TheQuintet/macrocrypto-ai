"""Tests for price alert API routes."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes import (
    get_db,
    create_price_alert,
    get_price_alerts,
    get_price_alert,
    update_price_alert,
    delete_price_alert,
    trigger_alert_manually,
)
from app.models.alert import (
    AlertStatus,
    AlertType,
    HistoryEventType,
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
    """Provide a mocked price alert."""
    item = MagicMock()
    item.id = uuid4()
    item.user_id = uuid4()
    item.threshold_price = 50000.0
    item.status = AlertStatus.ACTIVE
    item.alert_type = list(AlertType)[0]
    item.asset = "BTC"
    item.created_at = datetime(2026, 1, 1)

    item.to_dict.return_value = {
        "id": str(item.id),
        "user_id": str(item.user_id),
        "threshold_price": 50000.0,
        "status": AlertStatus.ACTIVE.value,
        "asset": "BTC",
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
        """Yield the database session and close it."""
        mock_session = MagicMock()

        with patch(
            "app.api.routes.SessionLocal",
            return_value=mock_session,
        ):
            generator = get_db()

            assert next(generator) is mock_session

            generator.close()

        mock_session.close.assert_called_once_with()

    def test_closes_session_when_generator_finishes(self):
        """Close the database session when the generator finishes."""
        mock_session = MagicMock()

        with patch(
            "app.api.routes.SessionLocal",
            return_value=mock_session,
        ):
            generator = get_db()

            assert next(generator) is mock_session

            with pytest.raises(StopIteration):
                next(generator)

        mock_session.close.assert_called_once_with()


class TestCreatePriceAlert:
    """Tests for creating price alerts."""

    @pytest.mark.asyncio
    async def test_create_price_alert_success(self, db, user_id):
        """Create a price alert successfully."""
        alert_data = MagicMock()

        alert_data.user_id = user_id
        alert_data.threshold_price = 50000.0
        alert_data.alert_type = list(AlertType)[0].value
        alert_data.asset = "BTC"
        alert_data.one_time = True
        alert_data.name = "BTC price alert"
        alert_data.description = "Test alert"
        alert_data.notify_in_app = True
        alert_data.notify_email = False

        mock_query(db, count=0)

        created_alert = MagicMock()
        created_alert.id = uuid4()
        created_alert.to_dict.return_value = {
            "id": str(created_alert.id),
            "asset": "BTC",
            "threshold_price": 50000.0,
        }

        with patch(
            "app.api.routes.settings.MAX_ALERTS_PER_USER",
            10,
        ), patch(
            "app.api.routes.PriceAlert",
            return_value=created_alert,
        ) as model, patch(
            "app.api.routes.AlertHistory"
        ) as history_model:

            result = await create_price_alert(
                alert_data=alert_data,
                db=db,
            )

        assert result == created_alert.to_dict.return_value

        model.assert_called_once()
        history_model.assert_called_once()

        db.add.assert_any_call(created_alert)
        db.add.assert_called_with(history_model.return_value)

        assert db.commit.call_count == 2
        db.refresh.assert_called_once_with(created_alert)

    @pytest.mark.asyncio
    async def test_create_price_alert_rejects_when_limit_reached(
        self,
        db,
        user_id,
    ):
        """Reject creation when the user's active alert limit is reached."""
        alert_data = MagicMock()
        alert_data.user_id = user_id

        mock_query(db, count=10)

        with patch(
            "app.api.routes.settings.MAX_ALERTS_PER_USER",
            10,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await create_price_alert(
                    alert_data=alert_data,
                    db=db,
                )

        assert exc_info.value.status_code == 400
        assert "Maximum alerts per user" in exc_info.value.detail

        db.add.assert_not_called()
        db.commit.assert_not_called()


class TestGetPriceAlerts:
    """Tests for listing price alerts."""

    @pytest.mark.asyncio
    async def test_returns_alerts(
        self,
        db,
        user_id,
        alert,
    ):
        """Return alerts for a user."""
        mock_query(
            db,
            result=[alert],
            count=1,
        )

        result = await get_price_alerts(
            user_id=user_id,
            status=None,
            alert_type=None,
            limit=50,
            offset=0,
            db=db,
        )

        assert result == {
            "total": 1,
            "limit": 50,
            "offset": 0,
            "alerts": [
                alert.to_dict.return_value,
            ],
        }

        alert.to_dict.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_returns_empty_list(
        self,
        db,
        user_id,
    ):
        """Return an empty list when the user has no alerts."""
        mock_query(
            db,
            result=[],
            count=0,
        )

        result = await get_price_alerts(
            user_id=user_id,
            status=None,
            alert_type=None,
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
    async def test_applies_pagination(
        self,
        db,
        user_id,
        alert,
    ):
        """Apply limit and offset to the query."""
        query = mock_query(
            db,
            result=[alert],
            count=25,
        )

        result = await get_price_alerts(
            user_id=user_id,
            status=None,
            alert_type=None,
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
    async def test_filters_by_valid_status(
        self,
        db,
        user_id,
    ):
        """Filter alerts by a valid status."""
        query = mock_query(
            db,
            result=[],
            count=0,
        )

        valid_status = list(AlertStatus)[0].value

        await get_price_alerts(
            user_id=user_id,
            status=valid_status,
            alert_type=None,
            limit=50,
            offset=0,
            db=db,
        )

        assert query.filter.call_count == 2

    @pytest.mark.asyncio
    async def test_filters_by_valid_alert_type(
        self,
        db,
        user_id,
    ):
        """Filter alerts by a valid alert type."""
        query = mock_query(
            db,
            result=[],
            count=0,
        )

        valid_alert_type = list(AlertType)[0].value

        await get_price_alerts(
            user_id=user_id,
            status=None,
            alert_type=valid_alert_type,
            limit=50,
            offset=0,
            db=db,
        )

        assert query.filter.call_count == 2


class TestGetPriceAlert:
    """Tests for retrieving a single price alert."""

    @pytest.mark.asyncio
    async def test_returns_alert_when_found(
        self,
        db,
        alert_id,
        alert,
    ):
        """Return the requested alert."""
        mock_query(db, result=alert)

        result = await get_price_alert(
            alert_id=alert_id,
            db=db,
        )

        assert result == alert.to_dict.return_value
        alert.to_dict.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_raises_404_when_alert_missing(
        self,
        db,
        alert_id,
    ):
        """Raise 404 when the alert does not exist."""
        mock_query(db, result=None)

        with pytest.raises(HTTPException) as exc_info:
            await get_price_alert(
                alert_id=alert_id,
                db=db,
            )

        assert exc_info.value.status_code == 404
        assert str(alert_id) in exc_info.value.detail


class TestUpdatePriceAlert:
    """Tests for updating price alerts."""

    @pytest.mark.asyncio
    async def test_update_alert_success(
        self,
        db,
        alert_id,
        alert,
    ):
        """Update alert fields successfully."""
        mock_query(db, result=alert)

        update_data = MagicMock()
        update_data.model_dump.return_value = {
            "threshold_price": 60000.0,
            "asset": "BTC",
            "name": "Updated alert",
            "description": "Updated description",
            "notify_email": True,
        }

        result = await update_price_alert(
            alert_id=alert_id,
            alert_data=update_data,
            db=db,
        )

        assert alert.threshold_price == 60000.0
        assert alert.asset == "BTC"
        assert alert.name == "Updated alert"
        assert alert.description == "Updated description"
        assert alert.notify_email is True

        assert isinstance(alert.updated_at, datetime)

        db.commit.assert_called_once_with()
        db.refresh.assert_called_once_with(alert)

        assert result == alert.to_dict.return_value

    @pytest.mark.asyncio
    async def test_update_alert_with_all_supported_fields(
        self,
        db,
        alert_id,
        alert,
    ):
        """Update all supported alert fields."""
        mock_query(db, result=alert)

        valid_alert_type = list(AlertType)[0].value

        update_data = MagicMock()
        update_data.model_dump.return_value = {
            "threshold_price": 75000.0,
            "alert_type": valid_alert_type,
            "asset": "ETH",
            "one_time": False,
            "name": "Updated",
            "description": "Updated description",
            "notify_in_app": False,
            "notify_email": True,
        }

        await update_price_alert(
            alert_id=alert_id,
            alert_data=update_data,
            db=db,
        )

        assert alert.threshold_price == 75000.0
        assert alert.alert_type == AlertType(valid_alert_type)
        assert alert.asset == "ETH"
        assert alert.one_time is False
        assert alert.name == "Updated"
        assert alert.description == "Updated description"
        assert alert.notify_in_app is False
        assert alert.notify_email is True

        db.commit.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_update_alert_status_creates_history(
        self,
        db,
        alert_id,
        alert,
    ):
        """Create history when alert status changes."""
        mock_query(db, result=alert)

        previous_status = alert.status

        new_status = next(
            status
            for status in AlertStatus
            if status != previous_status
        )

        update_data = MagicMock()
        update_data.model_dump.return_value = {
            "status": new_status.value,
        }

        with patch(
            "app.api.routes.AlertHistory"
        ) as history_model:

            await update_price_alert(
                alert_id=alert_id,
                alert_data=update_data,
                db=db,
            )

        assert alert.status == new_status
        history_model.assert_called_once()

        db.add.assert_called_once_with(
            history_model.return_value
        )

        assert db.commit.call_count == 2

    @pytest.mark.asyncio
    async def test_update_alert_without_status_change(
        self,
        db,
        alert_id,
        alert,
    ):
        """Do not create history when status does not change."""
        mock_query(db, result=alert)

        update_data = MagicMock()
        update_data.model_dump.return_value = {
            "name": "Updated name",
        }

        with patch(
            "app.api.routes.AlertHistory"
        ) as history_model:

            await update_price_alert(
                alert_id=alert_id,
                alert_data=update_data,
                db=db,
            )

        history_model.assert_not_called()
        db.add.assert_not_called()
        db.commit.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_update_alert_not_found(
        self,
        db,
        alert_id,
    ):
        """Raise 404 when updating a missing alert."""
        mock_query(db, result=None)

        update_data = MagicMock()
        update_data.model_dump.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            await update_price_alert(
                alert_id=alert_id,
                alert_data=update_data,
                db=db,
            )

        assert exc_info.value.status_code == 404
        db.commit.assert_not_called()


class TestDeletePriceAlert:
    """Tests for deleting price alerts."""

    @pytest.mark.asyncio
    async def test_delete_alert_success(
        self,
        db,
        alert_id,
        alert,
    ):
        """Delete an existing alert."""
        mock_query(db, result=alert)

        result = await delete_price_alert(
            alert_id=alert_id,
            db=db,
        )

        assert result is None
        db.delete.assert_called_once_with(alert)
        db.commit.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_delete_alert_not_found(
        self,
        db,
        alert_id,
    ):
        """Raise 404 when deleting a missing alert."""
        mock_query(db, result=None)

        with pytest.raises(HTTPException) as exc_info:
            await delete_price_alert(
                alert_id=alert_id,
                db=db,
            )

        assert exc_info.value.status_code == 404
        db.delete.assert_not_called()
        db.commit.assert_not_called()


class TestTriggerAlertManually:
    """Tests for manually triggering alerts."""

    @pytest.mark.asyncio
    async def test_trigger_alert_success(
        self,
        db,
        alert_id,
        alert,
    ):
        """Trigger an active alert successfully."""
        mock_query(db, result=alert)

        engine = MagicMock()

        with patch(
            "app.api.routes.AlertEngine",
            return_value=engine,
        ) as engine_class:

            result = await trigger_alert_manually(
                alert_id=alert_id,
                db=db,
            )

        engine_class.assert_called_once_with(db)

        engine._handle_triggered_alert.assert_called_once_with(
            alert,
            alert.threshold_price,
        )

        db.refresh.assert_called_once_with(alert)

        assert result == alert.to_dict.return_value

    @pytest.mark.asyncio
    async def test_trigger_alert_not_found(
        self,
        db,
        alert_id,
    ):
        """Raise 404 when triggering a missing alert."""
        mock_query(db, result=None)

        with pytest.raises(HTTPException) as exc_info:
            await trigger_alert_manually(
                alert_id=alert_id,
                db=db,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_trigger_alert_requires_active_status(
        self,
        db,
        alert_id,
        alert,
    ):
        """Reject triggering an inactive alert."""
        inactive_status = next(
            status
            for status in AlertStatus
            if status != AlertStatus.ACTIVE
        )

        alert.status = inactive_status

        mock_query(db, result=alert)

        with patch(
            "app.api.routes.AlertEngine"
        ) as engine_class:

            with pytest.raises(HTTPException) as exc_info:
                await trigger_alert_manually(
                    alert_id=alert_id,
                    db=db,
                )

        assert exc_info.value.status_code == 400
        assert "Alert is not active" in exc_info.value.detail

        engine_class.assert_not_called()
        db.refresh.assert_not_called()