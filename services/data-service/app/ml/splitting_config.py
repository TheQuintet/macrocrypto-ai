from pydantic import BaseModel, Field, model_validator


class SplitConfig(BaseModel):
  """Configuration parameters for train/val/test chronological splitting,

  walk-forward cross-validation, and leakage purge/embargo buffers.
  """

  train_ratio: float = Field(
      default=0.80, gt=0.0, lt=1.0, description="Proportion of data for training."
  )
  val_ratio: float = Field(
      default=0.10, gt=0.0, lt=1.0, description="Proportion of data for validation."
  )
  test_ratio: float = Field(
      default=0.10, gt=0.0, lt=1.0, description="Proportion of data for holdout test."
  )
  purge_window: int = Field(
      default=7,
      ge=0,
      description=(
          "Purge window (days) between train and val to eliminate rolling"
          " feature overlap."
      ),
  )
  embargo_window: int = Field(
      default=7,
      ge=0,
      description="Embargo window (days) between val and test sets.",
  )
  n_walk_forward_splits: int = Field(
      default=5,
      ge=1,
      description="Number of folds for walk-forward rolling cross-validation.",
  )

  @model_validator(mode="after")
  def validate_ratios(self) -> "SplitConfig":
    total = self.train_ratio + self.val_ratio + self.test_ratio
    if abs(total - 1.0) > 1e-6:
      raise ValueError(
          f"Split ratios must sum to 1.0, got {total:.4f} (train:"
          f" {self.train_ratio}, val: {self.val_ratio}, test:"
          f" {self.test_ratio})"
      )
    return self