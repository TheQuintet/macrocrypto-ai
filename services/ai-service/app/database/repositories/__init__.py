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
    - ExportHistoryRepository: writes export_history rows, reads
      export request history (A2.1)
    - EventImpactRepository: writes historical_event_impacts rows,
      reads per-event BTC reaction history (A5.1)
"""

from app.database.repositories.correlation_repository import (
    CorrelationRepository,
    CorrelationRow,
)
from app.database.repositories.export_history_repository import (
    ExportHistoryRepository,
    ExportHistoryRow,
)
from app.database.repositories.event_impact_repository import (
    EventImpactRepository,
    EventImpactRow,
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
    "ExportHistoryRepository",
    "ExportHistoryRow",
    "EventImpactRepository",
    "EventImpactRow",
]