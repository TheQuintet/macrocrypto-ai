from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.btc_price import Base
# Import models so SQLAlchemy registers them with Base.metadata
from app.models.btc_price import BTCPrice
from app.models.macro_indicator import MacroIndicator
from app.models.btc_dominance import BTCDominance
from app.models.macro_regime import MacroRegime
from app.models.regime_performance import RegimePerformance
from app.models.current_regime import CurrentRegime
from app.models.regime_event_analysis import RegimeEventAnalysis
from app.models.economic_event import EconomicEvent
from app.models.user_calendar_preference import UserCalendarPreference

from app.config import settings
import logging


"""
Module that configures the SQLAlchemy engine and session factory.

It reads DATABASE_URL and pooling parameters from the application settings
to establish database connectivity.

At startup:
- Creates database tables
- Enables TimescaleDB hypertables where required
"""

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def init_db():
    """
    Initialize database connection and create TimescaleDB hypertables.
    """
    try:
        # Create tables if they do not already exist
        Base.metadata.create_all(bind=engine)

        with engine.connect() as connection:

            # Verify database connection
            connection.execute(text("SELECT 1"))

            # Create btc_prices hypertable
            connection.execute(
                text(
                    """
                    SELECT create_hypertable(
                        'btc_prices',
                        'time',
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    )
                    """
                )
            )

            # Create macro indicators hypertable
            connection.execute(
                text(
                    """
                    SELECT create_hypertable(
                        'macro_indicators',
                        'time',
                        chunk_time_interval => INTERVAL '1 year',
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    )
                    """
                )
            )

            # Create btc_dominance hypertable
            connection.execute(
                text(
                    """
                    SELECT create_hypertable(
                        'btc_dominance',
                        'time',
                        chunk_time_interval => INTERVAL '1 year',
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    )
                    """
                )
            )

            connection.commit()

        logger.info("Database connection initialized")
        logger.info("TimescaleDB hypertable initialized")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise