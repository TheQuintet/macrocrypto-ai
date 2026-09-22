"""Shared FastAPI dependencies for the API layer.

This module provides dependency-injection helpers used by routers.
Each dependency is an async generator or async function that FastAPI
invokes per request and injects into route handlers.

Currently provides:
    - get_repository: yields a PredictionRepository bound to a
      transactional AsyncSession

Future dependencies (to be added in later branches):
    - get_current_user (JWT auth)
    - rate limiter
    - Redis cache client
"""

import logging
from typing import AsyncIterator

from app.database.engine import session_scope
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)


logger = logging.getLogger(__name__)


# ============================================================
# DATABASE
# ============================================================
async def get_repository() -> AsyncIterator[PredictionRepository]:
    """Yield a PredictionRepository bound to a transactional session.

    The session is opened via `session_scope()`, which commits on
    successful exit and rolls back on exception. FastAPI calls this
    per request and disposes of the session when the request ends.

    Yields:
        A PredictionRepository instance.
    """
    async with session_scope() as session:
        yield PredictionRepository(session)