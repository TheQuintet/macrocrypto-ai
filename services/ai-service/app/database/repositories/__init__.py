"""AI Service — Database repositories.

Each repository encapsulates reads and writes for one domain table
(or a small group of related tables). Repositories take an
AsyncSession in their constructor, so they are trivially mockable
in unit tests.

Available repositories:
    - PredictionRepository: reads BTC + macro source data, writes
      BTC predictions
    - PerformanceRepository: writes prediction_performance rows,
      reads aggregated metrics
    - ThresholdRepository: writes threshold_breaches rows, reads
      recent breaches
    - ModelPerformanceRepository: writes model_performance rows,
      reads per-model aggregate metrics and history (M7)
    - CorrelationRepository: writes btc_macro_correlation rows,
      reads BTC-vs-macro correlations (A1.1)
"""

from app.database.repositories.correlation_repository import (
    CorrelationRepository,
    CorrelationRow,
)
from app.database.repositories.model_performance_repository import (
    ModelPerformanceRepository,
    ModelPerformanceRow,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
    PredictionRow,
)
from app.database.repositories.performance_repository import (
    PerformanceRepository,
    PerformanceRow,
)
from app.database.repositories.threshold_repository import (
    ThresholdBreachRow,
    ThresholdRepository,
)

__all__ = [
    "PredictionRepository",
    "PredictionRow",
    "PerformanceRepository",
    "PerformanceRow",
    "ThresholdRepository",
    "ThresholdBreachRow",
    "ModelPerformanceRepository",
    "ModelPerformanceRow",
    "CorrelationRepository",
    "CorrelationRow",
]