"""Pytest fixtures for data-service tests."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

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


# ============================================================
# SEED DATA FIXTURES
# ============================================================

@pytest.fixture
def seed_macro_indicators():
    """
    Seed macro indicator data for integration tests.

    Inserts test indicators into the database and cleans up
    only the rows created by this fixture.
    """
    session = SessionLocal()

    now = datetime.now(timezone.utc)

    inserted_rows = [
        {
            "indicator_name": "GDP Growth",
            "time": now - timedelta(days=1),
            "value": 2.5,
            "previous_value": 2.3,
            "change_percent": 8.7,
            "source": "FRED",
        },
        {
            "indicator_name": "Inflation Rate",
            "time": now - timedelta(days=1),
            "value": 3.2,
            "previous_value": 3.5,
            "change_percent": -8.57,
            "source": "FRED",
        },
        {
            "indicator_name": "Unemployment",
            "time": now - timedelta(days=1),
            "value": 4.1,
            "previous_value": 4.3,
            "change_percent": -4.65,
            "source": "BLS",
        },
    ]

    try:
        for row in inserted_rows:
            session.execute(
                text("""
                    INSERT INTO macro_indicators (
                        indicator_name,
                        time,
                        value,
                        previous_value,
                        change_percent,
                        source,
                        created_at
                    ) VALUES (
                        :indicator_name,
                        :time,
                        :value,
                        :previous_value,
                        :change_percent,
                        :source,
                        :created_at
                    )
                """),
                {
                    **row,
                    "created_at": now,
                },
            )

        session.commit()

        yield session

    except Exception:
        session.rollback()
        raise

    finally:
        for row in inserted_rows:
            session.execute(
                text("""
                    DELETE FROM macro_indicators
                    WHERE indicator_name = :indicator_name
                      AND time = :time
                """),
                {
                    "indicator_name": row["indicator_name"],
                    "time": row["time"],
                },
            )

        session.commit()
        session.close()

@pytest.fixture
def seed_current_regime():
    """
    Seed current regime data for integration tests.

    Inserts a test current regime into the database and cleans up
    after the test completes.
    """
    session = SessionLocal()

    try:
        # Insert test current regime
        now = datetime.now(timezone.utc)
        
        session.execute(
            text("""
                INSERT INTO current_regime (
                    regime_type,
                    confidence,
                    visual_indicator,
                    identified_at,
                    expires_at
                ) VALUES (
                    'growth',
                    85.0,
                    'bull',
                    :now,
                    :expires
                )
            """),
            {
                "now": now,
                "expires": now + timedelta(days=1)
            }
        )
        session.commit()
        
        yield session
        
    except Exception as e:
        session.rollback()
        raise e
        
    finally:
        # Clean up after test
        session.execute(text("DELETE FROM current_regime"))
        session.commit()
        session.close()


@pytest.fixture
def seed_regime_history():
    """
    Seed regime history data for integration tests.

    Inserts test regime history records and cleans up
    after the test completes.
    """
    session = SessionLocal()

    try:
        # Insert test regime history
        now = datetime.now(timezone.utc)
        
        # Check if table exists first
        result = session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'regime_history'
            )
        """))
        table_exists = result.scalar()
        
        if not table_exists:
            # If table doesn't exist, skip seeding
            yield session
            return
        
        session.execute(
            text("""
                INSERT INTO regime_history (
                    regime_type,
                    start_date,
                    end_date,
                    performance_data
                ) VALUES 
                    ('growth', :start1, :end1, '{"avg_return": 15.5, "max_drawdown": -5.2, "volatility": 12.3, "sharpe_ratio": 1.2}'),
                    ('recession', :start2, :end2, '{"avg_return": -10.2, "max_drawdown": -25.1, "volatility": 18.7, "sharpe_ratio": -0.5}')
            """),
            {
                "start1": now - timedelta(days=90),
                "end1": now - timedelta(days=30),
                "start2": now - timedelta(days=120),
                "end2": now - timedelta(days=91),
            }
        )
        session.commit()
        
        yield session
        
    except Exception as e:
        session.rollback()
        # Don't raise - just log that table doesn't exist
        print(f"Note: regime_history table may not exist: {e}")
        yield session
        
    finally:
        try:
            session.execute(text("DELETE FROM regime_history"))
            session.commit()
        except:
            pass
        session.close()