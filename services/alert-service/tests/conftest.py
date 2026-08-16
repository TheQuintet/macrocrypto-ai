# import pytest
# from sqlalchemy.orm import Session

# from app.database.session import engine, SessionLocal
# from app.models.alert import Base


# @pytest.fixture(scope="session", autouse=True)
# def setup_database():
#     """
#     Create all tables in the database once per test session 
#     and drop them when the test suite finishes.
#     """
#     Base.metadata.create_all(bind=engine)
#     yield
#     Base.metadata.drop_all(bind=engine)


# @pytest.fixture
# def db_session() -> Session:
#     """
#     Provide a fresh, isolated database session for each test function.
#     Rolls back any changes after the test completes so tests remain independent.
#     """
#     connection = engine.connect()
#     transaction = connection.begin()
    
#     # Bind the session to the active transaction connection
#     session = SessionLocal(bind=connection)
    
#     yield session
    
#     session.close()
#     transaction.rollback()
#     connection.close()

import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.database.session import engine, SessionLocal
from app.models.alert import Base, PriceAlert, AlertType, AlertStatus


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
def db_session() -> Session:
    """
    Provide a fresh, isolated database session for each test function.
    Rolls back any changes after the test completes so tests remain independent.
    """
    connection = engine.connect()
    transaction = connection.begin()
    
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


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