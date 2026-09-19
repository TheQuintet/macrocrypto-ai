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
    - prediction_performance: Core table for evaluation metrics
    - PredictionRepository, PredictionRow: prediction read/write repo
    - PerformanceRepository, PerformanceRow: performance read/write repo
    - validate_prediction_row, validate_prediction_rows: validators
    - validate_performance_row, validate_performance_rows: validators
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
    prediction_performance,
)
from app.database.repositories import (
    PerformanceRepository,
    PerformanceRow,
    PredictionRepository,
    PredictionRow,
)
from app.database.validators import (
    validate_performance_row,
    validate_performance_rows,
    validate_prediction_row,
    validate_prediction_rows,
    VALID_CONFIDENCE_LEVELS,
    VALID_HORIZONS,
    VALID_MARKET_CONDITIONS,
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
    "prediction_performance",
    "PredictionRepository",
    "PredictionRow",
    "PerformanceRepository",
    "PerformanceRow",
    "validate_prediction_row",
    "validate_prediction_rows",
    "validate_performance_row",
    "validate_performance_rows",
    "VALID_HORIZONS",
    "VALID_CONFIDENCE_LEVELS",
    "VALID_MARKET_CONDITIONS",
    "run_migrations",
]