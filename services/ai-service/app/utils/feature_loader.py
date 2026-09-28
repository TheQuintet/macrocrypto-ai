import os
import joblib
import logging
from typing import Tuple, Optional, Any
import pandas as pd
from pathlib import Path
from app.config import settings
from app.ai.models.feature_utils import (
    CONSTANT_FEATURE_COLUMNS_ATTR,
    constant_feature_columns,
)

logger = logging.getLogger(__name__)

class FeatureLoader:
    """Loads scaled feature parquet files and scaler artifacts from the data-service processed directory."""

    def __init__(self, shared_dir: Optional[str] = None) -> None:
        self._constant_feature_columns: Optional[list[str]] = None
        if shared_dir:
            self.shared_dir = shared_dir
        else:
            # Default path pointing to data-service/app/data/processed relative to ai-service
            # ai-service is at services/ai-service, data-service is at services/data-service (or project root)
            root_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.shared_dir = getattr(
                settings, 
                "shared_data_dir", 
                str(root_dir / "data-service" / "app" / "data" / "processed")
            )

    def _get_partition_path(self, partition_name: str) -> str:
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

    def load_partition(self, partition_name: str) -> pd.DataFrame:
        """Load a partition, excluding columns constant in the training data."""
        path = self._get_partition_path(partition_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Partition file not found: {path}")
        
        logger.info(f"Loading partition '{partition_name}' from {path}")
        data = pd.read_parquet(path)

        if partition_name == "train":
            self._constant_feature_columns = constant_feature_columns(data)
        elif self._constant_feature_columns is None:
            train_path = self._get_partition_path("train")
            if not os.path.exists(train_path):
                raise FileNotFoundError(
                    "Training partition is required to identify constant "
                    f"features: {train_path}"
                )
            training_data = pd.read_parquet(train_path)
            self._constant_feature_columns = constant_feature_columns(
                training_data
            )

        constant_columns = self._constant_feature_columns or []
        columns_to_drop = [
            column for column in constant_columns if column in data.columns
        ]
        data = data.drop(columns=columns_to_drop)
        data.attrs[CONSTANT_FEATURE_COLUMNS_ATTR] = constant_columns.copy()
        if columns_to_drop:
            logger.info(
                "Dropped training-constant feature columns from '%s': %s",
                partition_name,
                columns_to_drop,
            )
        return data

    def load_scaler(self) -> Any:
        """Load the fitted feature scaler pickle file."""
        path = os.path.join(self.shared_dir, "feature_scaler.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Scaler artifact not found at: {path}")
        
        logger.info(f"Loading feature scaler from {path}")
        return joblib.load(path)

    def prepare_training_data(self, partition_name: str, target_column: str = "target_next_price") -> Tuple[pd.DataFrame, pd.Series]:
            """Load partition data and split into scaled features (X) and target (y)."""
            df = self.load_partition(partition_name)
            
            # Check for target_next_price or common fallbacks
            col_to_use = target_column
            if col_to_use not in df.columns:
                for alt in ["target_next_price", "y", "target", "label"]:
                    if alt in df.columns:
                        col_to_use = alt
                        break
                
            if col_to_use not in df.columns:
                raise ValueError(
                    f"Target column '{target_column}' is missing from partition '{partition_name}'. "
                    f"Available columns: {list(df.columns)}"
                )
            
            y_target = df[col_to_use]
            X_scaled = df.drop(columns=[col_to_use])
            
            return X_scaled, y_target