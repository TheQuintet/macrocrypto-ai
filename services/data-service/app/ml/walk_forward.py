import numpy as np
import pandas as pd
from app.ml.splitting_config import SplitConfig


class WalkForwardSplitter:
  """Time-series cross-validation splitter with support for chronological

  train/val/test splits, purging, and embargoing to prevent leakage.
  Powered by SplitConfig for robust Pydantic parameter validation.
  """

  def __init__(self, config: SplitConfig = None):
    self.config = config or SplitConfig()
    self.train_ratio = self.config.train_ratio
    self.val_ratio = self.config.val_ratio
    self.test_ratio = self.config.test_ratio
    self.purge_window = self.config.purge_window
    self.embargo_window = self.config.embargo_window
    self.n_splits = self.config.n_walk_forward_splits

  def split_indices(self, n_samples: int):
    """Computes absolute start and end index bounds for train, val, and test sets."""
    train_end = int(n_samples * self.train_ratio)
    val_start = train_end + self.purge_window
    val_end = val_start + int(n_samples * self.val_ratio)
    test_start = val_end + self.embargo_window
    test_end = n_samples

    return {
        "train": (0, train_end),
        "val": (val_start, val_end),
        "test": (test_start, test_end),
    }

  def get_walk_forward_folds(self, n_samples: int):
    """Generates rolling expanding-window train/val splits natively."""
    train_end_limit = int(n_samples * (self.train_ratio + self.val_ratio))
    indices = np.arange(train_end_limit)
    fold_size = len(indices) // (self.n_splits + 1)

    for i in range(1, self.n_splits + 1):
      split_point = fold_size * i
      train_idx = indices[:split_point]
      val_end = min(split_point + fold_size, train_end_limit)
      val_idx = indices[split_point:val_end]

      # Apply purge window to the end of train set to prevent feature overlap leakage
      if len(train_idx) > self.purge_window:
        train_idx = train_idx[: -self.purge_window]

      if len(val_idx) > 0 and len(train_idx) > 0:
        yield train_idx, val_idx