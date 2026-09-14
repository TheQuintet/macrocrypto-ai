"""AI Service — Database package.

Exposes the async engine helpers, Core table definitions,
repositories, validators, and the migration runner.

Public API:
    - get_engine: returns the global async engine
    - get_session_factory: returns the global session factory
    - session_scope: async context manager for transactions
    - dispose_engine: clean shutdown helper
    - metadata: SQLAlchemy MetaData (shared root for all tables)
    - btc_prices, macro_indicators, btc_predictions: Core tables
    - PredictionRepository, PredictionRow: prediction read/write repo
    - validate_prediction_row, validate_prediction_rows: validators
    - run_migrations: apply pending SQL migrations
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
from app.database.validators import (
    validate_prediction_row,
    validate_prediction_rows,
    VALID_CONFIDENCE_LEVELS,
    VALID_HORIZONS,
)
from app.database.migrations_runner import run_migrations

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
    "validate_prediction_row",
    "validate_prediction_rows",
    "VALID_HORIZONS",
    "VALID_CONFIDENCE_LEVELS",
    "run_migrations",
]