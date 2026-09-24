from typing import List, Literal
from pydantic import BaseModel, Field


class ScalerConfig(BaseModel):
  scaler_type: Literal["robust", "standard", "minmax"] = Field(
      default="robust",
      description=(
          "Default to RobustScaler to handle cryptocurrency volatility,"
          " macroeconomic shocks, and heavy tails."
      ),
  )
  target_column: str = Field(
      default="target_next_price",
      description="The target column to exempt from feature scaling.",
  )
  date_column: str = Field(
      default="observation_date",
      description="The calendar date column to exempt.",
  )
  exclude_suffixes: List[str] = Field(
      default_factory=lambda: [
          "_timestamp",
          "_is_missing",
          "_is_imputed",
      ],
      description="Suffixes identifying timestamps and binary status flags.",
  )
  explicit_exclusions: List[str] = Field(
      default_factory=lambda: ["warmup_complete"],
      description="Additional specific columns to exempt from scaling.",
  )