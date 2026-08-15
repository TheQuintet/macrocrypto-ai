from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.alert import Base
import logging


"""
Module that configures the SQLAlchemy engine and session factory.

It reads DATABASE_URL and pooling parameters from the application settings
to establish database connectivity.
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
    Initialize database connection and create tables.
    """
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        with engine.connect() as connection:
            # Verify database connection
            connection.execute(text("SELECT 1"))
            connection.commit()

        logger.info("✅ Database connection initialized")
        logger.info("✅ Alert service tables created")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise