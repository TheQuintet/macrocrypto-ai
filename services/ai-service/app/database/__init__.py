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
    - threshold_breaches: Core table for threshold breach history
    - TABLE_* constants: canonical table names
    - PredictionRepository, PredictionRow: prediction read/write repo
    - PerformanceRepository, PerformanceRow: performance read/write repo
    - ThresholdRepository, ThresholdBreachRow: breach read/write repo
    - Validators for prediction and performance rows
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
    threshold_breaches,
    TABLE_BTC_PREDICTIONS,
    TABLE_BTC_PRICES,
    TABLE_MACRO_INDICATORS,
    TABLE_PREDICTION_PERFORMANCE,
    TABLE_THRESHOLD_BREACHES,
)
from app.database.repositories import (
    PerformanceRepository,
    PerformanceRow,
    PredictionRepository,
    PredictionRow,
    ThresholdBreachRow,
    ThresholdRepository,
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
    "threshold_breaches",
    "TABLE_BTC_PRICES",
    "TABLE_MACRO_INDICATORS",
    "TABLE_BTC_PREDICTIONS",
    "TABLE_PREDICTION_PERFORMANCE",
    "TABLE_THRESHOLD_BREACHES",
    "PredictionRepository",
    "PredictionRow",
    "PerformanceRepository",
    "PerformanceRow",
    "ThresholdRepository",
    "ThresholdBreachRow",
    "validate_prediction_row",
    "validate_prediction_rows",
    "validate_performance_row",
    "validate_performance_rows",
    "VALID_HORIZONS",
    "VALID_CONFIDENCE_LEVELS",
    "VALID_MARKET_CONDITIONS",
    "run_migrations",
]