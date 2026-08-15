"""Unit tests for history service"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.services.history_service import HistoryService
from app.models.alert import PriceAlert, AlertStatus, AlertType, AlertHistory, HistoryEventType


class TestHistoryService:
    """Test cases for HistoryService."""

    @pytest.fixture
    def history_service(self, db_session):
        """Create history service instance."""
        return HistoryService(db_session)

    @pytest.fixture
    def sample_alert(self, db_session):
        """Create a sample alert for testing."""
        alert = PriceAlert(
            id=uuid4(),
            user_id=uuid4(),
            threshold_price=85000.00,
            alert_type=AlertType.REACHES,
            asset="BTC/USD",
            status=AlertStatus.ACTIVE,
            one_time=True,
            notify_in_app=True,
            notify_email=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        return alert

    @pytest.fixture
    def sample_history(self, db_session, sample_alert):
        """Create sample history entries."""
        history1 = AlertHistory(
            alert_id=sample_alert.id,
            event_type=HistoryEventType.EVALUATION,
            event_source="engine",
            triggered_price=84000.00,
            threshold_price=85000.00,
            alert_type="reaches",
            previous_status=AlertStatus.ACTIVE,
            new_status=AlertStatus.ACTIVE,
            triggered_at=datetime.utcnow()
        )
        db_session.add(history1)

        history2 = AlertHistory(
            alert_id=sample_alert.id,
            event_type=HistoryEventType.TRIGGERED,
            event_source="engine",
            triggered_price=85000.00,
            threshold_price=85000.00,
            alert_type="reaches",
            previous_status=AlertStatus.ACTIVE,
            new_status=AlertStatus.TRIGGERED,
            triggered_at=datetime.utcnow()
        )
        db_session.add(history2)

        db_session.commit()
        return history1, history2

    def test_get_alert_history(
        self, history_service, sample_alert, sample_history
    ):
        """Test getting history for a specific alert."""
        total, history = history_service.get_alert_history(
            alert_id=sample_alert.id,
            limit=10,
            offset=0
        )

        assert total == 2
        assert len(history) == 2

    def test_get_alert_history_filtered_by_event_type(
        self, history_service, sample_alert, sample_history
    ):
        """Test getting history filtered by event type."""
        total, history = history_service.get_alert_history(
            alert_id=sample_alert.id,
            event_type="triggered",
            limit=10,
            offset=0
        )

        assert total == 1
        assert len(history) == 1
        assert history[0].event_type == HistoryEventType.TRIGGERED

    def test_get_alert_history_filtered_by_date_range(
        self, history_service, sample_alert, sample_history
    ):
        """Test getting history filtered by date range."""
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow() + timedelta(days=1)

        total, history = history_service.get_alert_history(
            alert_id=sample_alert.id,
            start_date=start_date,
            end_date=end_date,
            limit=10,
            offset=0
        )

        assert total == 2
        assert len(history) == 2

    def test_get_user_history(
        self, history_service, db_session, sample_alert, sample_history
    ):
        """Test getting history for a user."""
        total, history = history_service.get_user_history(
            user_id=sample_alert.user_id,
            limit=10,
            offset=0
        )

        assert total == 2
        assert len(history) == 2

    def test_get_triggered_history(
        self, history_service, sample_alert, sample_history
    ):
        """Test getting triggered history for a user."""
        total, history = history_service.get_triggered_history(
            user_id=sample_alert.user_id,
            limit=10,
            offset=0
        )

        assert total == 1
        assert len(history) == 1
        assert history[0].event_type == HistoryEventType.TRIGGERED

    def test_log_alert_acknowledged(
        self, history_service, db_session, sample_alert
    ):
        """Test logging alert acknowledged."""
        history_service.log_alert_acknowledged(
            alert_id=sample_alert.id,
            ip_address="127.0.0.1"
        )

        total, history = history_service.get_alert_history(
            alert_id=sample_alert.id,
            limit=10,
            offset=0
        )

        assert total == 1
        assert history[0].event_type == HistoryEventType.ACKNOWLEDGED
        assert history[0].ip_address == "127.0.0.1"

    def test_log_alert_dismissed(
        self, history_service, db_session, sample_alert
    ):
        """Test logging alert dismissed."""
        history_service.log_alert_dismissed(
            alert_id=sample_alert.id,
            ip_address="127.0.0.1"
        )

        total, history = history_service.get_alert_history(
            alert_id=sample_alert.id,
            limit=10,
            offset=0
        )

        assert total == 1
        assert history[0].event_type == HistoryEventType.DISMISSED

    def test_log_alert_disabled(
        self, history_service, db_session, sample_alert
    ):
        """Test logging alert disabled."""
        history_service.log_alert_disabled(
            alert_id=sample_alert.id,
            ip_address="127.0.0.1"
        )

        total, history = history_service.get_alert_history(
            alert_id=sample_alert.id,
            limit=10,
            offset=0
        )

        assert total == 1
        assert history[0].event_type == HistoryEventType.DISABLED

    def test_get_alert_trigger_count(
        self, history_service, sample_alert, sample_history
    ):
        """Test getting trigger count for an alert."""
        count = history_service.get_alert_trigger_count(sample_alert.id)

        assert count == 1

    def test_get_user_trigger_count(
        self, history_service, sample_alert, sample_history
    ):
        """Test getting trigger count for a user."""
        count = history_service.get_user_trigger_count(sample_alert.user_id)

        assert count == 1

    def test_cleanup_old_history(
        self, history_service, db_session, sample_alert
    ):
        """Test cleaning up old history."""
        # Create old history entry
        old_history = AlertHistory(
            alert_id=sample_alert.id,
            event_type=HistoryEventType.EVALUATION,
            event_source="engine",
            triggered_price=84000.00,
            threshold_price=85000.00,
            alert_type="reaches",
            previous_status=AlertStatus.ACTIVE,
            new_status=AlertStatus.ACTIVE,
            triggered_at=datetime.utcnow() - timedelta(days=60)
        )
        db_session.add(old_history)
        db_session.commit()

        # Cleanup history older than 30 days
        deleted = history_service.cleanup_old_history(days_to_keep=30)

        assert deleted == 1

        # Verify old history is gone
        total, history = history_service.get_alert_history(
            alert_id=sample_alert.id,
            limit=10,
            offset=0
        )

        assert total == 0