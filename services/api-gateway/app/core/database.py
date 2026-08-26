"""Database connection and session management.

This module provides the database engine, session factory, and dependency
injection for FastAPI routes.
"""

import logging
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

from app.core.config import settings

logger = logging.getLogger(settings.SERVICE_NAME)


# ============================================
# DATABASE ENGINE
# ============================================

def create_database_engine() -> Engine:
    """Create and configure the SQLAlchemy database engine.

    Returns:
        Engine: Configured SQLAlchemy engine.
    """
    # Build database URL from settings
    # Format: postgresql://user:password@host:port/database
    database_url = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

    # Create engine with connection pooling
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=settings.DB_POOL_RECYCLE,  # Recycle connections after this time
        echo=settings.DB_ECHO,  # Log SQL queries (debug only)
    )

    # Add event listener for connection checkout
    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log when a connection is checked out from the pool."""
        logger.debug(f"Database connection checked out (pool size: {engine.pool.size()})")

    logger.info(f"✅ Database engine created: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    return engine


# ============================================
# SESSION FACTORY
# ============================================

# Create engine instance
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Keep objects usable after commit
)


# ============================================
# DEPENDENCY INJECTION
# ============================================

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes to get a database session.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()

    Yields:
        Session: SQLAlchemy session for the request.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get a standalone database session (for background tasks).

    Returns:
        Session: SQLAlchemy session.
    """
    return SessionLocal()


# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_database() -> None:
    """Initialize the database by creating all tables.

    This function should be called at application startup.
    """
    try:
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def close_database_connections() -> None:
    """Close all database connections.

    This function should be called at application shutdown.
    """
    try:
        engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise


# ============================================
# HEALTH CHECK HELPERS
# ============================================

def check_database_health() -> bool:
    """Check if the database is accessible.

    Returns:
        bool: True if database is healthy, False otherwise.
    """
    try:
        from sqlalchemy import text
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_database_status() -> dict:
    """Get detailed database status information.

    Returns:
        dict: Database status information.
    """
    try:
        from sqlalchemy import text
        status = {
            "connected": False,
            "pool_size": engine.pool.size(),
            "pool_checked_in": engine.pool.checkedin(),
            "pool_overflow": engine.pool.overflow(),
            "pool_total": engine.pool.total(),
        }

        with SessionLocal() as session:
            result = session.execute(text("SELECT version()")).scalar()
            status["connected"] = True
            status["version"] = result

        return status
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return {"connected": False, "error": str(e)}