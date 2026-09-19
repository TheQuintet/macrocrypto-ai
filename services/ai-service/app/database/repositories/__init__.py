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
"""

from app.database.repositories.prediction_repository import (
    PredictionRepository,
    PredictionRow,
)
from app.database.repositories.performance_repository import (
    PerformanceRepository,
    PerformanceRow,
)

__all__ = [
    "PredictionRepository",
    "PredictionRow",
    "PerformanceRepository",
    "PerformanceRow",
]