"""Async database engine and session management for the AI Service.

This module provides the SQLAlchemy 2.0 async engine and session
infrastructure used by all repositories. It handles:
    - Lazy engine creation from settings.database_url
    - Async session factory (async_sessionmaker)
    - Transaction-scoped context manager (session_scope)
    - Graceful shutdown (dispose_engine)

Design:
    - The engine is created lazily on first use so importing this
      module does not require a live database.
    - One engine per process (module-level global). SQLAlchemy's
      async engine maintains its own connection pool internally.
    - Sessions are created per-transaction and closed automatically
      by the session_scope context manager.

Usage:
    from app.database.engine import session_scope

    async with session_scope() as session:
        result = await session.execute(select(...))
        ...
        # commit happens automatically on successful exit
        # rollback happens automatically on exception
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# MODULE STATE
# ============================================================
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


# ============================================================
# ENGINE
# ============================================================
def get_engine() -> AsyncEngine:
    """Return the global async engine, creating it on first call.

    The engine is built from `settings.async_database_url` (which
    converts `postgresql://` to `postgresql+asyncpg://`). Connection
    pool defaults are:
        - pool_size=5 (baseline connections)
        - max_overflow=10 (burst connections)
        - pool_pre_ping=True (validate stale connections)
        - echo=False (SQL logging off by default)

    SQL echo can be enabled via the `DEBUG_SQL` env var by setting
    `settings.debug` to a value that includes "sql" — but that's
    reserved for later; for now echo is off.

    Returns:
        AsyncEngine instance.
    """
    global _engine

    if _engine is None:
        url = settings.async_database_url
        logger.info(
            f"Creating async database engine (url={_mask_url(url)})"
        )

        _engine = create_async_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
            future=True,
        )

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the global async session factory, creating it on first call.

    The session factory is bound to the global engine. Sessions
    produced by this factory have:
        - expire_on_commit=False (attributes remain accessible after commit)
        - autoflush=False (explicit flush preferred for predictability)

    Returns:
        async_sessionmaker bound to the global engine.
    """
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    return _session_factory


# ============================================================
# SESSION CONTEXT MANAGER
# ============================================================
@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional async session scope.

    Opens a new session from the global factory, yields it, and:
        - Commits on successful exit
        - Rolls back on any exception
        - Always closes the session

    Example:
        async with session_scope() as session:
            result = await session.execute(select(MyTable))
            # ... on exit: commit is automatic

    Yields:
        AsyncSession scoped to a transaction.
    """
    factory = get_session_factory()

    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ============================================================
# SHUTDOWN
# ============================================================
async def dispose_engine() -> None:
    """Dispose of the global engine and reset module state.

    Called during application shutdown to close all pooled
    connections cleanly. Safe to call multiple times; subsequent
    calls to get_engine() will create a fresh engine.
    """
    global _engine, _session_factory

    if _engine is not None:
        logger.info("Disposing async database engine")
        await _engine.dispose()

    _engine = None
    _session_factory = None


# ============================================================
# INTERNAL HELPERS
# ============================================================
def _mask_url(url: str) -> str:
    """Mask the password portion of a database URL for logging.

    Args:
        url: A database URL string.

    Returns:
        URL with password replaced by "***", or the original URL
        if no password is present.
    """
    if "@" not in url or "://" not in url:
        return url

    try:
        scheme, rest = url.split("://", 1)
        credentials, host = rest.split("@", 1)
        if ":" in credentials:
            user, _ = credentials.split(":", 1)
            return f"{scheme}://{user}:***@{host}"
        return url
    except Exception:
        return url