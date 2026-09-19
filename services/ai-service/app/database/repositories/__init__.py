"""AI Service — Database repositories.

Each repository encapsulates reads and writes for one domain table
(or a small group of related tables). Repositories take an
AsyncSession in their constructor, so they are trivially mockable
in unit tests.

Available repositories:
    - PredictionRepository: reads BTC + macro source data, writes
      BTC predictions
"""

from app.database.repositories.prediction_repository import (
    PredictionRepository,
    PredictionRow,
)

__all__ = [
    "PredictionRepository",
    "PredictionRow",
]