"""AI Service — Database package.

Exposes the async engine helpers, Core table definitions, and
repositories used by the service.

Public API:
    - get_engine: returns the global async engine
    - get_session_factory: returns the global session factory
    - session_scope: async context manager for transactions
    - dispose_engine: clean shutdown helper
    - metadata: SQLAlchemy MetaData (shared root for all tables)
    - btc_prices, macro_indicators, btc_predictions: Core tables
    - PredictionRepository, PredictionRow: prediction read/write repo
"""

from app.database.engine import (
    dispose_engine,
    get_engine,
    get_session_factory,
    session_scope,
)
from app.database.tables import (
    btc_predictions,
    btc_prices,
    macro_indicators,
    metadata,
)
from app.database.repositories import (
    PredictionRepository,
    PredictionRow,
)

__all__ = [
    "dispose_engine",
    "get_engine",
    "get_session_factory",
    "session_scope",
    "metadata",
    "btc_prices",
    "macro_indicators",
    "btc_predictions",
    "PredictionRepository",
    "PredictionRow",
]