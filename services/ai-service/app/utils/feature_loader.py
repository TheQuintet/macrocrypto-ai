"""Feature loader for the AI Service.

Reads scaled feature partitions and the fitted scaler artifact from
the data-service's shared output directory. This is the entry point
for the manual file-path pipeline (see ``app/ai/pipeline.py``) and
for any code that needs to consume the canonical 47-column dataset
outside the live DB path.

Design:
    - The directory is configured via ``settings.shared_data_dir``.
      In Docker/K8s, this is typically a read-only volume mount
      shared with the data-service.
    - Partitions are individual parquet files (one per split):
      train, val, test, live_frontier.
    - The scaler is a single pickle file (feature_scaler.pkl) used
      to standardize features during training.
    - This loader does NOT do any transformation. It loads files
      as-is. Any renaming, target selection, or split logic lives
      in the caller.

Usage:
    from app.utils.feature_loader import FeatureLoader

    loader = FeatureLoader()
    df = loader.load_partition("train")
    scaler = loader.load_scaler()
    X, y = loader.prepare_training_data("train")

Notes on the canonical feature set:
    - The parquet files carry the full 47-column contract used by
      all six model variants (Prophet, XGBoost, LightGBM × fresh /
      warm-incremental).
    - Column names use the model-expected vocabulary
      (e.g. ``btc_volume``, ``federal_funds_rate``), NOT the legacy
      Postgres names (``volume``, ``interest_rate``).
    - The target column is typically named ``target_next_price`` but
      common fallbacks (``y``, ``target``, ``label``) are supported
      by ``prepare_training_data``.
"""

import logging
import os
from typing import Any, Optional, Tuple

import joblib
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class FeatureLoader:
    """Loader for scaled feature parquet files and scaler artifacts.

    The loader reads from a single directory that the data-service
    writes to. By default this comes from ``settings.shared_data_dir``
    (an environment-configurable path), which in containerized
    deployments is a read-only volume mount.

    All methods are read-only and raise on missing files rather than
    silently returning empty frames — callers are expected to treat
    a missing partition as a hard failure.
    """

    def __init__(self, shared_dir: Optional[str] = None) -> None:
        """Initialize the loader.

        Args:
            shared_dir: Optional override for the shared directory.
                When provided, this takes precedence over
                ``settings.shared_data_dir``. Useful for tests and
                for tooling that operates on a non-default location.
                When None (default), reads from
                ``settings.shared_data_dir``.
        """
        if shared_dir:
            self.shared_dir = shared_dir
        else:
            self.shared_dir = settings.shared_data_dir

        logger.debug(
            f"FeatureLoader initialized with shared_dir='{self.shared_dir}'"
        )

    # ============================================================
    # PARTITION PATHS
    # ============================================================
    def _get_partition_path(self, partition_name: str) -> str:
        """Return the full path to a partition parquet file.

        Args:
            partition_name: One of "train", "val", "test",
                "live_frontier".

        Returns:
            Absolute path to the partition file.

        Raises:
            ValueError: If the partition name is not recognized.
        """
        filename_map = {
            "train": "train_scaled.parquet",
            "val": "val_scaled.parquet",
            "test": "test_scaled.parquet",
            "live_frontier": "live_frontier_scaled.parquet",
        }
        if partition_name not in filename_map:
            raise ValueError(
                f"Unknown partition '{partition_name}'. "
                f"Valid options are: {list(filename_map.keys())}"
            )
        return os.path.join(self.shared_dir, filename_map[partition_name])

    # ============================================================
    # LOADING
    # ============================================================
    def load_partition(self, partition_name: str) -> pd.DataFrame:
        """Load a scaled feature partition from disk.

        Reads the parquet file for the requested partition and
        returns it as a pandas DataFrame. The DataFrame contains the
        canonical 47-column set (45 features plus the timestamp and
        target), with column names matching the model adapters'
        expectations.

        Args:
            partition_name: One of "train", "val", "test",
                "live_frontier".

        Returns:
            DataFrame with the full feature set for the partition.

        Raises:
            ValueError: If the partition name is not recognized.
            FileNotFoundError: If the parquet file does not exist at
                the expected path.
        """
        path = self._get_partition_path(partition_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Partition file not found: {path}")

        logger.info(f"Loading partition '{partition_name}' from {path}")
        return pd.read_parquet(path)

    def load_scaler(self) -> Any:
        """Load the fitted feature scaler from disk.

        The scaler is written by the data-service alongside the
        parquet partitions and is used to standardize feature values
        at training time. The returned object is whatever was pickled
        by the data-service — typically a scikit-learn transformer.

        Returns:
            The fitted scaler object.

        Raises:
            FileNotFoundError: If the scaler file does not exist.
        """
        path = os.path.join(self.shared_dir, "feature_scaler.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Scaler artifact not found at: {path}")

        logger.info(f"Loading feature scaler from {path}")
        return joblib.load(path)

    # ============================================================
    # CONVENIENCE
    # ============================================================
    def prepare_training_data(
        self,
        partition_name: str,
        target_column: str = "target_next_price",
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Load a partition and split it into features (X) and target (y).

        Resolves the target column by trying the requested name first
        and falling back to common alternatives. This tolerates small
        naming differences across data-service versions without
        requiring a code change.

        Args:
            partition_name: One of "train", "val", "test",
                "live_frontier".
            target_column: Preferred name of the target column.
                Defaults to "target_next_price".

        Returns:
            Tuple of (X_scaled, y_target):
                - X_scaled: DataFrame with all non-target columns.
                - y_target: Series with the target values.

        Raises:
            ValueError: If no valid target column can be found in the
                loaded partition.
            FileNotFoundError: If the partition file is missing.
        """
        df = self.load_partition(partition_name)

        # Resolve the target column with fallbacks.
        col_to_use = target_column
        if col_to_use not in df.columns:
            for alt in ["target_next_price", "y", "target", "label"]:
                if alt in df.columns:
                    col_to_use = alt
                    break

        if col_to_use not in df.columns:
            raise ValueError(
                f"Target column '{target_column}' is missing from "
                f"partition '{partition_name}'. "
                f"Available columns: {list(df.columns)}"
            )

        y_target = df[col_to_use]
        X_scaled = df.drop(columns=[col_to_use])

        return X_scaled, y_target