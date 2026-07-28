from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

"""
Module that configures the SQLAlchemy engine and session factory.

It reads DATABASE_URL and pooling parameters from the application settings
to establish database connectivity. Call init_db() at startup to verify
the connection and ensure the database is reachable.
"""
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
    Initialize database connection.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("Database connection initialized")

    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise