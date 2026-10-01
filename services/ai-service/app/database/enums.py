"""Enumerations for the AI Service database layer.

Contains small, shared enums used by repositories, jobs, and the
CLI. Kept in a dedicated module so that consumers can import them
without pulling in the full repository (which has heavier
dependencies like SQLAlchemy and pandas).

Enums defined here:
    - FeaturePartition: named partitions in the canonical feature
      dataset.
    - FeatureContext: what a caller is doing when requesting a
      training frame. Resolves to a default FeaturePartition.
"""

from enum import Enum


# ============================================================
# FEATURE PARTITION
# ============================================================
class FeaturePartition(str, Enum):
    """Named partitions in the canonical feature dataset.

    Each value corresponds to a physical parquet file in the
    data-service output directory (and, later, to a partition
    filter in the features DB table):

        TRAIN          -> "train"         -> train_scaled.parquet
        VAL            -> "val"           -> val_scaled.parquet
        TEST           -> "test"          -> test_scaled.parquet
        LIVE_FRONTIER  -> "live_frontier" -> live_frontier_scaled.parquet

    Subclassing `str` makes the enum values directly usable as
    strings (e.g. in dict keys, log messages, and path construction)
    without needing to call `.value`.
    """

    TRAIN = "train"
    VAL = "val"
    TEST = "test"
    LIVE_FRONTIER = "live_frontier"


# ============================================================
# FEATURE CONTEXT
# ============================================================
class FeatureContext(str, Enum):
    """What a caller is doing when requesting a training frame.

    Used by the repository's dispatcher to resolve the default
    partition for the file-based feature source. Each context
    maps to exactly one partition:

        TRAINING    -> TRAIN
        VALIDATION  -> VAL
        TEST        -> TEST
        PREDICTION  -> LIVE_FRONTIER

    Callers pass a context instead of a raw partition name so the
    intent is explicit at the call site and the default mapping
    lives in one place.
    """

    TRAINING = "training"
    VALIDATION = "validation"
    TEST = "test"
    PREDICTION = "prediction"